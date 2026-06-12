"""
Character persistence — save/load AgentCharacter to SQLite.

Built on top of core.py (the fastc-core-sqlite Python port).
Provides schema creation, character CRUD, and batch operations.
"""

import json
import time
from typing import Optional, Dict, Any, List, Tuple

from .core import Db, DbError, exec, query, next, get_int, get_text, open, close, Cap


# ─── Schema ───────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS characters (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name  TEXT    NOT NULL,
    domain      TEXT    NOT NULL,
    level       INTEGER NOT NULL DEFAULT 1,
    xp          INTEGER NOT NULL DEFAULT 0,
    xp_to_next  INTEGER NOT NULL DEFAULT 10,
    total_requests INTEGER NOT NULL DEFAULT 0,
    success_streak  INTEGER NOT NULL DEFAULT 0,
    fail_streak     INTEGER NOT NULL DEFAULT 0,
    best_streak     INTEGER NOT NULL DEFAULT 0,
    worst_slump     INTEGER NOT NULL DEFAULT 0,
    tick        INTEGER NOT NULL DEFAULT 0,

    -- Stats
    perception  REAL NOT NULL DEFAULT 10.0,
    dexterity   REAL NOT NULL DEFAULT 10.0,
    intelligence REAL NOT NULL DEFAULT 10.0,
    wisdom      REAL NOT NULL DEFAULT 10.0,
    charisma    REAL NOT NULL DEFAULT 10.0,
    constitution REAL NOT NULL DEFAULT 10.0,

    -- Class
    current_class   TEXT NOT NULL DEFAULT 'UNDEFINED',
    previous_class  TEXT,
    class_trajectory TEXT DEFAULT '[]',
    class_reasons    TEXT DEFAULT '[]',

    -- Arc snapshot (JSON)
    arc_json    TEXT DEFAULT '{}',

    -- Dreams (JSON arrays)
    dreams_json TEXT DEFAULT '[]',
    patterns_json TEXT DEFAULT '[]',

    -- Metadata
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,

    -- One agent per combo
    UNIQUE(agent_name, domain)
);

CREATE TABLE IF NOT EXISTS experiences (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name  TEXT    NOT NULL,
    domain      TEXT    NOT NULL,
    exp_id      INTEGER NOT NULL,
    input_text  TEXT    NOT NULL,
    success     INTEGER NOT NULL,
    reward      REAL    NOT NULL,
    tick        INTEGER NOT NULL,
    created_at  REAL    NOT NULL,
    UNIQUE(agent_name, domain, exp_id)
);

CREATE INDEX IF NOT EXISTS idx_characters_domain ON characters(domain);
CREATE INDEX IF NOT EXISTS idx_characters_level ON characters(level DESC);
CREATE INDEX IF NOT EXISTS idx_experiences_agent ON experiences(agent_name, domain);
CREATE INDEX IF NOT EXISTS idx_experiences_tick ON experiences(tick);
"""


def create_schema(db: Db):
    """Create all tables needed for character persistence.

    Idempotent — safe to call multiple times.
    """
    statements = [s.strip() for s in SCHEMA_SQL.split(";") if s.strip()]
    for stmt in statements:
        exec(db, stmt + ";")


# ─── CharacterStore ──────────────────────────────────────────────────

class CharacterStore:
    """High-level persistence for AgentCharacter objects.

    Wraps a Db handle with character save/load/delete operations.
    Uses the same capability model as core.py.

    Usage:
        db = open("fleet-characters.db")
        store = CharacterStore(db)
        create_schema(db)

        store.save(agent)
        loaded = store.load("chord-agent", "chord")
        all_agents = store.list_characters()
        close(db)
    """

    def __init__(self, db: Db):
        self._db = db

    # ─── Save / Load ──────────────────────────────────────────

    def save(self, agent_char: Any) -> int:
        """Save an AgentCharacter to the database. Creates or updates.

        Accepts any object with a to_dict() method that returns
        the standard AgentCharacter dict format.

        Returns:
            Row ID of the saved character
        """
        d = agent_char.to_dict()
        now = time.time()
        stats = d.get('stats', {})
        class_traj = d.get('class_trajectory', [])
        if isinstance(class_traj, list):
            class_traj_str = json.dumps(class_traj)
        else:
            class_traj_str = class_traj

        # Extract arc JSON
        arc = d.get('arc', {})
        arc_json = json.dumps(arc)

        # Extract dreams
        dream = d.get('dream', {})
        dreams_data = dream.get('experiences', [])
        patterns_data = dream.get('patterns', [])
        dreams_json = json.dumps(dreams_data)
        patterns_json = json.dumps(patterns_data)

        sql = """
        INSERT INTO characters (
            agent_name, domain, level, xp, xp_to_next,
            total_requests, success_streak, fail_streak,
            best_streak, worst_slump, tick,
            perception, dexterity, intelligence, wisdom,
            charisma, constitution,
            current_class, previous_class,
            class_trajectory, class_reasons,
            arc_json, dreams_json, patterns_json,
            created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?
        )
        ON CONFLICT(agent_name, domain) DO UPDATE SET
            level=excluded.level,
            xp=excluded.xp,
            xp_to_next=excluded.xp_to_next,
            total_requests=excluded.total_requests,
            success_streak=excluded.success_streak,
            fail_streak=excluded.fail_streak,
            best_streak=excluded.best_streak,
            worst_slump=excluded.worst_slump,
            tick=excluded.tick,
            perception=excluded.perception,
            dexterity=excluded.dexterity,
            intelligence=excluded.intelligence,
            wisdom=excluded.wisdom,
            charisma=excluded.charisma,
            constitution=excluded.constitution,
            current_class=excluded.current_class,
            previous_class=excluded.previous_class,
            class_trajectory=excluded.class_trajectory,
            class_reasons=excluded.class_reasons,
            arc_json=excluded.arc_json,
            dreams_json=excluded.dreams_json,
            patterns_json=excluded.patterns_json,
            updated_at=excluded.updated_at
        RETURNING id;
        """
        params = (
            d.get('name', d.get('agent_name', '')),
            d.get('domain', ''),
            d.get('level', 1),
            d.get('xp', 0),
            d.get('xp_to_next', 10),
            d.get('total_requests', 0),
            d.get('success_streak', 0),
            d.get('fail_streak', 0),
            d.get('best_streak', 0),
            d.get('worst_slump', 0),
            d.get('tick', 0),
            stats.get('perception', 10.0),
            stats.get('dexterity', 10.0),
            stats.get('intelligence', 10.0),
            stats.get('wisdom', 10.0),
            stats.get('charisma', 10.0),
            stats.get('constitution', 10.0),
            d.get('class', 'UNDEFINED'),
            d.get('previous_class', None),
            class_traj_str,
            json.dumps([]),  # class_reasons placeholder
            arc_json,
            dreams_json,
            patterns_json,
            now, now
        )

        self._db._conn.execute(sql, params)
        self._db._conn.commit()
        cur = self._db._conn.execute("SELECT last_insert_rowid()")
        return cur.fetchone()[0]

    def load(self, agent_name: str, domain: str) -> Optional[Dict[str, Any]]:
        """Load a character from the database by agent name and domain.

        Returns:
            Dict matching AgentCharacter.to_dict() format, or None if not found
        """
        sql = "SELECT * FROM characters WHERE agent_name=? AND domain=?;"
        cur = self._db._conn.execute(sql, (agent_name, domain))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def load_all(self) -> List[Dict[str, Any]]:
        """Load all characters from the database.

        Returns:
            List of character dicts
        """
        sql = "SELECT * FROM characters ORDER BY level DESC, domain;"
        cur = self._db._conn.execute(sql)
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def delete(self, agent_name: str, domain: str) -> bool:
        """Delete a character from the database.

        Returns:
            True if deleted, False if not found
        """
        cursor = self._db._conn.execute(
            "DELETE FROM characters WHERE agent_name=? AND domain=?;",
            (agent_name, domain)
        )
        self._db._conn.commit()
        return cursor.rowcount > 0

    def delete_all(self) -> int:
        """Delete all characters. Use with extreme caution.

        Returns:
            Number of deleted rows
        """
        cur = self._db._conn.execute("DELETE FROM characters;")
        self._db._conn.commit()
        return cur.rowcount

    def vacuum(self):
        """Recover disk space from deleted rows."""
        self._db._conn.execute("VACUUM;")
        self._db._conn.commit()

    # ─── Experiences ───────────────────────────────────────────

    def save_experience(self, agent_name: str, domain: str,
                        exp: Dict[str, Any]):
        """Save one experience record for an agent."""
        now = time.time()
        sql = """
        INSERT OR REPLACE INTO experiences
            (agent_name, domain, exp_id, input_text, success, reward,
             tick, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self._db._conn.execute(sql, (
            agent_name, domain,
            exp.get('id', 0),
            exp.get('input', ''),
            1 if exp.get('success', True) else 0,
            exp.get('reward', 0.0),
            exp.get('tick', 0),
            now,
        ))
        self._db._conn.commit()

    def load_experiences(self, agent_name: str, domain: str,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Load recent experiences for an agent."""
        sql = """
        SELECT * FROM experiences
        WHERE agent_name=? AND domain=?
        ORDER BY tick DESC
        LIMIT ?;
        """
        cur = self._db._conn.execute(sql, (agent_name, domain, limit))
        rows = []
        for r in cur.fetchall():
            rows.append({
                'id': r['exp_id'],
                'input': r['input_text'],
                'success': bool(r['success']),
                'reward': r['reward'],
                'tick': r['tick'],
                'created_at': r['created_at'],
            })
        return rows

    # ─── Query helpers ─────────────────────────────────────────

    def count(self) -> int:
        """Total number of characters stored."""
        cur = self._db._conn.execute("SELECT COUNT(*) FROM characters;")
        return cur.fetchone()[0]

    def count_experiences(self) -> int:
        """Total number of experiences stored."""
        cur = self._db._conn.execute("SELECT COUNT(*) FROM experiences;")
        return cur.fetchone()[0]

    def top_by_level(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Top characters by level."""
        cur = self._db._conn.execute(
            "SELECT * FROM characters ORDER BY level DESC, xp DESC LIMIT ?;",
            (limit,)
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def top_by_stat(self, stat: str = "charisma",
                    limit: int = 5) -> List[Dict[str, Any]]:
        """Top characters by a specific stat."""
        valid = ["perception", "dexterity", "intelligence",
                 "wisdom", "charisma", "constitution"]
        if stat not in valid:
            raise ValueError(
                f"Invalid stat '{stat}'. Valid: {valid}"
            )
        cur = self._db._conn.execute(
            f"SELECT * FROM characters ORDER BY {stat} DESC LIMIT ?;",
            (limit,)
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def search(self, query_str: str) -> List[Dict[str, Any]]:
        """Search characters by name or domain."""
        like = f"%{query_str}%"
        cur = self._db._conn.execute(
            "SELECT * FROM characters WHERE agent_name LIKE ? "
            "OR domain LIKE ? ORDER BY level DESC LIMIT 20;",
            (like, like)
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    # ─── Internal ──────────────────────────────────────────────

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a sqlite3.Row to an AgentCharacter-style dict."""
        arc_json = row['arc_json'] or '{}'
        dreams_json = row['dreams_json'] or '[]'
        patterns_json = row['patterns_json'] or '[]'
        class_traj_str = row['class_trajectory'] or '[]'

        return {
            'agent': f"fleet-midi-{row['domain']}",
            'name': row['agent_name'],
            'domain': row['domain'],
            'level': row['level'],
            'xp': row['xp'],
            'xp_to_next': row['xp_to_next'],
            'class': row['current_class'],
            'previous_class': row['previous_class'],
            'class_trajectory': json.loads(class_traj_str),
            'stats': {
                'perception': round(row['perception'], 1),
                'dexterity': round(row['dexterity'], 1),
                'intelligence': round(row['intelligence'], 1),
                'wisdom': round(row['wisdom'], 1),
                'charisma': round(row['charisma'], 1),
                'constitution': round(row['constitution'], 1),
            },
            'total_requests': row['total_requests'],
            'success_streak': row['success_streak'],
            'best_streak': row['best_streak'],
            'worst_slump': row['worst_slump'],
            'tick': row['tick'],
            'arc': json.loads(arc_json),
            'dream': {
                'experiences': json.loads(dreams_json),
                'patterns': json.loads(patterns_json),
            },
        }
