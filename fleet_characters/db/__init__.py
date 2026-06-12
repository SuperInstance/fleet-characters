"""
fleet-sqlite — capability-typed SQLite persistence for the fleet character system.

Port of SuperInstance/fastc-core-sqlite into Python.
Keeps the same clean API: opaque handles, typed column accessors,
capability-gated file access.

The capability policies are advisory in Python (no compiler-enforced
cap gates), but the API shape mirrors the fastC original so any
agent familiar with `use sqlite::*` can use this module without
a mental model shift.
"""

from .core import (
    open,
    exec,
    query,
    next,
    get_int,
    get_text,
    close,
    Db,
    Cursor,
    Row,
    DbError,
    Cap,
)

from .persistence import (
    CharacterStore,
    create_schema,
)

__all__ = [
    "open",
    "exec",
    "query",
    "next",
    "get_int",
    "get_text",
    "close",
    "Db",
    "Cursor",
    "Row",
    "DbError",
    "Cap",
    "CharacterStore",
    "create_schema",
]
