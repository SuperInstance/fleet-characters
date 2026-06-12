"""
capability-typed SQLite persistence for the fleet character system.

Mirrors SuperInstance/fastc-core-sqlite's surface.
Opaque handles, typed column accessors, capability-gated file access.
"""

import sqlite3
import os
import threading
from typing import Optional, Any, List, Tuple, Callable
from enum import Enum


# ─── Capability tokens ────────────────────────────────────────────────

class Cap(Enum):
    """Capability tokens mirroring fastC's capability system.
    
    In fastC these are compiler-enforced; here they're advisory
    runtime guards that prevent accidental file system misuse.
    """
    FS_READ = "fs_read"      # Read-only file access
    FS_WRITE = "fs_write"    # Write-capable file access
    NET = "net"              # Network access
    MEM = "mem"              # Memory-only (no persistence)


# ─── Error type matching fastC's SqliteError enum ─────────────────────

class DbError(Exception):
    """Mirrors fastC's SqliteError enum.
    
    Variants:
        CannotOpen    — Database file could not be opened/created
        SyntaxError   — SQL is malformed
        BindFailed    — Parameter binding failed
        BusyOrLocked  — Database is busy or locked (SQLITE_BUSY/SQLITE_LOCKED)
        CapError      — Insufficient capability for the operation
        Other         — Other SQLite errors with SQLite error code
    """
    
    class Kind(Enum):
        CANNOT_OPEN = "CannotOpen"
        SYNTAX_ERROR = "SyntaxError"
        BIND_FAILED = "BindFailed"
        BUSY_OR_LOCKED = "BusyOrLocked"
        CAP_ERROR = "CapError"
        OTHER = "Other"
    
    def __init__(self, kind: Kind, message: str = "", sqlite_code: int = 0):
        self.kind = kind
        self.sqlite_code = sqlite_code
        full_msg = f"{kind.value}: {message}" if message else kind.value
        super().__init__(full_msg)
    
    @classmethod
    def from_sqlite(cls, e: sqlite3.Error, sql: str = "") -> "DbError":
        code = getattr(e, "sqlite_errorcode", 0)
        if isinstance(e, sqlite3.OperationalError):
            msg = str(e)
            if "no such table" in msg or "syntax error" in msg:
                return cls(cls.Kind.SYNTAX_ERROR, msg, code)
            if "locked" in msg or "busy" in msg:
                return cls(cls.Kind.BUSY_OR_LOCKED, msg, code)
            return cls(cls.Kind.OTHER, msg, code)
        if isinstance(e, sqlite3.DatabaseError):
            return cls(cls.Kind.OTHER, str(e), code)
        return cls(cls.Kind.OTHER, str(e), code)


# ─── Opaque handles ───────────────────────────────────────────────────

class Row:
    """Opaque handle to one row from a result set.
    
    Wraps sqlite3.Row. Column access via get_int() / get_text() only.
    """
    def __init__(self, row: sqlite3.Row, columns: List[str]):
        self._row = row
        self._columns = columns
    
    @property
    def _col_count(self) -> int:
        return len(self._columns)


class Cursor:
    """Opaque handle to an active query cursor.
    
    Created by query(), advanced with next(). Exhaustion returns None.
    """
    def __init__(self, db_cursor: sqlite3.Cursor):
        self._cursor = db_cursor
        self._columns = [d[0] for d in db_cursor.description] if db_cursor.description else []
    
    def __del__(self):
        try:
            self._cursor.close()
        except Exception:
            pass


class Db:
    """Opaque handle to an open database.
    
    Created by open(). Consumed by close(). Must be explicitly closed.
    """
    def __init__(self, conn: sqlite3.Connection, cap: Cap = Cap.FS_WRITE):
        self._conn = conn
        self._cap = cap
        self._closed = False
        
        # Enable WAL mode for concurrent readers
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    
    def _check_not_closed(self):
        if self._closed:
            raise DbError(DbError.Kind.CANNOT_OPEN, "database is closed")
    
    def _check_cap(self, required: Cap):
        if self._cap == Cap.MEM and required == Cap.FS_WRITE:
            raise DbError(DbError.Kind.CAP_ERROR, 
                          f"operation requires {required.value}, but db opened with {self._cap.value}")


# ─── Core API surface ───────────────────────────────

def open(path: str, cap: Cap = Cap.FS_WRITE) -> Db:
    """Open a database handle.
    
    Mirrors fastC's `sqlite::open(path: Str, cap: ref(CapFsWrite)) -> res(Db, SqliteError)`.
    
    Args:
        path: File path to SQLite database, or ":memory:" for an in-memory DB
        cap: Capability token (FS_WRITE for persistent, MEM for in-memory)
    
    Returns:
        Db handle (opaque)
    
    Raises:
        DbError.CannotOpen if the database could not be opened
        DbError.CapError if path is a file but cap is MEM
    """
    if path != ":memory:" and cap == Cap.MEM:
        raise DbError(DbError.Kind.CAP_ERROR, 
                      f"cannot open file path '{path}' with Cap.MEM; use Cap.FS_WRITE")
    
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return Db(conn, cap)
    except sqlite3.Error as e:
        raise DbError(DbError.Kind.CANNOT_OPEN, str(e))


def exec(db: Db, sql: str) -> int:
    """Execute a non-query SQL statement.
    
    Mirrors fastC's `sqlite::exec(db: ref(Db), sql: Str) -> res(i32, SqliteError)`.
    
    Returns:
        Number of rows affected
    
    Raises:
        DbError on failure
    """
    db._check_not_closed()
    try:
        db._conn.execute(sql)
        db._conn.commit()
        return db._conn.total_changes
    except sqlite3.Error as e:
        raise DbError.from_sqlite(e, sql)


def query(db: Db, sql: str) -> Cursor:
    """Start a SELECT query.
    
    Mirrors fastC's `sqlite::query(db: ref(Db), sql: Str) -> res(Cursor, SqliteError)`.
    
    Returns:
        Cursor handle for use with next()
    
    Raises:
        DbError on failure
    """
    db._check_not_closed()
    try:
        cur = db._conn.execute(sql)
        return Cursor(cur)
    except sqlite3.Error as e:
        raise DbError.from_sqlite(e, sql)


def next(cursor: Cursor) -> Optional[Row]:
    """Advance a cursor and return the next row.
    
    Mirrors fastC's `sqlite::next(cursor: mref(Cursor)) -> opt(Row)`.
    
    Returns:
        Row if available, None when exhausted
    """
    row = cursor._cursor.fetchone()
    if row is None:
        return None
    return Row(row, cursor._columns)


def get_int(row: Row, col: int) -> int:
    """Get an integer column value from a row.
    
    Mirrors fastC's `sqlite::get_int(row: ref(Row), col: i32) -> i64`.
    
    Args:
        row: Row from next()
        col: Column index (0-based)
    
    Returns:
        Integer value
    
    Raises:
        DbError on out-of-range column
    """
    if col < 0 or col >= row._col_count:
        raise DbError(DbError.Kind.BIND_FAILED, f"column index {col} out of range [0, {row._col_count})")
    val = row._row[col]
    if val is None:
        return 0
    return int(val)


def get_text(row: Row, col: int) -> str:
    """Get a text column value from a row.
    
    Mirrors fastC's `sqlite::get_text(row: ref(Row), col: i32) -> Str`.
    
    Args:
        row: Row from next()
        col: Column index (0-based)
    
    Returns:
        String value (empty string for NULL)
    
    Raises:
        DbError on out-of-range column
    """
    if col < 0 or col >= row._col_count:
        raise DbError(DbError.Kind.BIND_FAILED, f"column index {col} out of range [0, {row._col_count})")
    val = row._row[col]
    if val is None:
        return ""
    return str(val)


def close(db: Db):
    """Close a database handle. Required before program exit.
    
    Mirrors fastC's `sqlite::close(db: Db) -> void`.
    
    Note: Unlike fastC, this is idempotent — calling close()
    on an already-closed handle is a no-op.
    """
    if db._closed:
        return
    db._closed = True
    try:
        db._conn.close()
    except Exception:
        pass
