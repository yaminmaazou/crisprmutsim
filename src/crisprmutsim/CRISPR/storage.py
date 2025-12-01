from collections.abc import Sequence
from contextlib import contextmanager
import json
import sqlite3 as db
from typing import Any, Literal

from crisprmutsim.CRISPR.crispr_array import CRISPRArray
from crisprmutsim.simulation.event import (
    IEventGenerator,
    event_generators_to_json,
)


def connect_file(filename: str) -> db.Connection:
    return db.connect(filename)


@contextmanager
def database(filename: str):
    con = connect_file(filename)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def store_meta(
    con: db.Connection,
    type: Literal["sim"] | Literal["file"],
    info: str = "",
) -> None:
    con.execute(
        """
        CREATE TABLE meta (
        type TEXT,
        info TEXT
        ) STRICT;
        """
    )

    con.execute(
        "INSERT INTO meta (type, info) VALUES (?, ?)",
        (type, info),
    )


def load_meta(con: db.Connection) -> dict[str, Any]:
    row = con.execute("SELECT * FROM meta").fetchone()
    if row is None:
        return {}

    return {
        "type": row[0],
        "info": row[1],
    }


def store_simulation_info(
    con: db.Connection,
    base_seed: int,
    end_time: float,
    array_length: int,
    repeat_length: int,
    event_generators: Sequence[IEventGenerator[Any, Any, Any]],
    num_runs: int,
    meta: str = "",
) -> None:
    con.execute(
        """
        CREATE TABLE simulation_info (
        base_seed INTEGER,
        end_time REAL,
        array_length INTEGER,
        repeat_length INTEGER,
        event_generators TEXT,
        num_runs INTEGER,
        meta TEXT
        ) STRICT;
        """
    )

    con.execute(
        "INSERT INTO simulation_info (base_seed, end_time, array_length, repeat_length, event_generators, num_runs, meta) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            base_seed,
            end_time,
            array_length,
            repeat_length,
            event_generators_to_json(event_generators),
            num_runs,
            meta,
        ),
    )


def load_simulation_info(con: db.Connection) -> dict[str, Any] | None:
    cur = con.cursor()
    row = cur.execute("SELECT * FROM simulation_info").fetchone()
    if row is None:
        return None

    return {
        "base_seed": row[0],
        "end_time": row[1],
        "array_length": row[2],
        "repeat_length": row[3],
        "event_generators": row[4],
        "num_runs": row[5],
        "meta": row[6],
    }


def store_arrays(con: db.Connection, arrays: Sequence[CRISPRArray]) -> None:
    db.register_adapter(list, json.dumps)
    db.register_adapter(tuple, json.dumps)
    db.register_adapter(set, lambda s: json.dumps(sorted(list(s))))  # type: ignore

    con.execute(
        """
        CREATE TABLE arrays (
        id TEXT PRIMARY KEY,
        cas_type TEXT,
        consensus_repeat TEXT,
        -- partly redundant array stats --
        array_length INTEGER,
        repeat_length INTEGER,
        mutation_count_consensus INTEGER,
        mutation_count_proximal INTEGER,
        mutation_count_distal INTEGER,
        mutation_diff_consensus TEXT,
        mutation_diff_proximal TEXT,
        mutation_diff_distal TEXT,
        patterns TEXT
        ) STRICT;
        """
    )

    con.executemany(
        """INSERT INTO arrays
        VALUES (:id, :cas_type, :consensus_repeat, :array_length, :repeat_length, :mutation_count_consensus, :mutation_count_proximal, :mutation_count_distal, :mutation_diff_consensus, :mutation_diff_proximal, :mutation_diff_distal, :patterns)""",
        [array.as_flat_dict() for array in arrays],
    )


def load_array(con: db.Connection, id: str) -> CRISPRArray | None:
    cur = con.cursor()
    # works according to docs, but typing is broken
    cur.row_factory = db.Row  # type: ignore
    row = cur.execute("SELECT * FROM arrays WHERE id = ?", (id,)).fetchone()

    return CRISPRArray.from_db_row(row) if row is not None else None


def load_arrays(
    con: db.Connection,
    min_array_length: int | None = None,
    max_array_length: int | None = None,
    min_repeat_length: int | None = None,
    max_repeat_length: int | None = None,
    cas_types: list[str] = [],
    patterns_to_exclude: list[int] = [],
) -> list[CRISPRArray]:
    """Load all arrays matching the filter criteria."""
    where_clause, params = _build_where_clause(
        min_array_length,
        max_array_length,
        min_repeat_length,
        max_repeat_length,
        cas_types,
        patterns_to_exclude,
    )

    cur = con.cursor()
    # works according to docs, but typing is broken
    cur.row_factory = db.Row  # type: ignore
    rows = cur.execute(
        f"SELECT * FROM arrays {where_clause} ORDER BY id", params
    ).fetchall()

    return [CRISPRArray.from_db_row(row) for row in rows]


def load_array_ids(
    con: db.Connection,
    min_array_length: int | None = None,
    max_array_length: int | None = None,
    min_repeat_length: int | None = None,
    max_repeat_length: int | None = None,
    cas_types: list[str] = [],
    patterns_to_exclude: list[int] = [],
) -> list[str]:
    where_clause, params = _build_where_clause(
        min_array_length,
        max_array_length,
        min_repeat_length,
        max_repeat_length,
        cas_types,
        patterns_to_exclude,
    )

    query = "SELECT id FROM arrays"
    if where_clause:
        query += " " + where_clause
    query += " ORDER BY id"
    rows = con.execute(query, params).fetchall()
    return [row[0] for row in rows]


def get_min_max_array_length(con: db.Connection) -> tuple[int, int]:
    row = con.execute(
        "SELECT MIN(array_length), MAX(array_length) FROM arrays"
    ).fetchone()
    return row[0], row[1]


def get_min_max_repeat_length(con: db.Connection) -> tuple[int, int]:
    row = con.execute(
        "SELECT MIN(repeat_length), MAX(repeat_length) FROM arrays"
    ).fetchone()
    return row[0], row[1]


def get_cas_types(con: db.Connection) -> list[str]:
    rows = con.execute(
        "SELECT DISTINCT cas_type FROM arrays ORDER BY cas_type"
    ).fetchall()
    return [row[0] for row in rows]


def _build_where_clause(
    min_array_length: int | None = None,
    max_array_length: int | None = None,
    min_repeat_length: int | None = None,
    max_repeat_length: int | None = None,
    cas_types: list[str] = [],
    patterns_to_exclude: list[int] = [],
) -> tuple[str, list[Any]]:
    where_conditions: list[str] = []
    params: list[Any] = []

    if min_array_length is not None:
        where_conditions.append("array_length >= ?")
        params.append(min_array_length)

    if max_array_length is not None:
        where_conditions.append("array_length <= ?")
        params.append(max_array_length)

    if min_repeat_length is not None:
        where_conditions.append("repeat_length >= ?")
        params.append(min_repeat_length)

    if max_repeat_length is not None:
        where_conditions.append("repeat_length <= ?")
        params.append(max_repeat_length)

    if len(cas_types) > 0:
        qmarks = ",".join("?" * len(cas_types))
        where_conditions.append(f"cas_type IN ({qmarks})")
        params.extend(cas_types)

    if len(patterns_to_exclude) > 0:
        pattern_exclusions: list[str] = []
        for pattern_val in patterns_to_exclude:
            if pattern_val == 0:  # exclude arrays with no patterns
                pattern_exclusions.append("json_array_length(patterns) = 0")
            else:
                pattern_exclusions.append(
                    f"EXISTS (SELECT 1 FROM json_each(patterns) WHERE value = ?)"
                )
                params.append(pattern_val)
        where_conditions.append(f"NOT ({' OR '.join(pattern_exclusions)})")

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    return where_clause, params
