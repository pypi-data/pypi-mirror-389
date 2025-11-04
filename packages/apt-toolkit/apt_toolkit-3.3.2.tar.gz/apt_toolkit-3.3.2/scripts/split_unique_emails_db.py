#!/usr/bin/env python3
"""
Split the consolidated emails SQLite database into sharded chunks smaller than
GitHub's 100 MB file limit.

Each shard preserves the original schema and primary keys so existing tooling
can treat the combined dataset as a single logical database via
`apt_toolkit.email_repository.open_email_database`.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from apt_toolkit.email_repository import (
    DEFAULT_DB_PATH,
    DEFAULT_SHARDS_DIR,
    SHARD_FILENAME_PREFIX,
    SHARD_FILENAME_SUFFIX,
)

ROWS_PER_SHARD_DEFAULT = 40_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split emails/unique_emails.db into <=100MB shard files."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Source SQLite database to split (default: emails/unique_emails.db).",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        default=DEFAULT_SHARDS_DIR,
        help="Destination directory for shard files (default: emails/shards).",
    )
    parser.add_argument(
        "--rows-per-shard",
        type=int,
        default=ROWS_PER_SHARD_DEFAULT,
        help=f"Approximate number of rows per shard (default: {ROWS_PER_SHARD_DEFAULT}).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing shard files in the destination directory.",
    )
    return parser.parse_args()


def fetch_schema(conn: sqlite3.Connection) -> Tuple[str, str]:
    """Return SQL snippets to recreate tables and indexes."""
    tables = [
        row["sql"]
        for row in conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        if row["sql"]
    ]
    indexes = [
        row["sql"]
        for row in conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'index'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        if row["sql"]
    ]
    return ";\n".join(tables), ";\n".join(indexes)


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    """Return the column list for a table in declaration order."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row["name"] for row in rows]


def chunk_ranges(
    conn: sqlite3.Connection, rows_per_shard: int
) -> Iterable[Tuple[int, int, int]]:
    """
    Yield (chunk_index, min_id, max_id) for each shard.

    Chunks are computed using the `emails` primary key to maintain stable joins
    with `email_records`.
    """
    total_rows = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
    if total_rows == 0:
        return []

    chunks = math.ceil(total_rows / rows_per_shard)
    cursor = conn.execute(
        "SELECT id FROM emails ORDER BY id"
    )
    ids = [row["id"] for row in cursor.fetchall()]

    ranges = []
    for index in range(chunks):
        start = index * rows_per_shard
        subset = ids[start : start + rows_per_shard]
        if not subset:
            break
        ranges.append((index, subset[0], subset[-1]))
    return ranges


def copy_chunk(
    src: sqlite3.Connection,
    dest_path: Path,
    schema_sql: str,
    index_sql: str,
    email_columns: Sequence[str],
    email_record_columns: Sequence[str],
    chunk_index: int,
    min_id: int,
    max_id: int,
) -> None:
    """Copy a slice of rows into a new shard database."""
    if dest_path.exists():
        dest_path.unlink()

    dest = sqlite3.connect(dest_path)
    dest.row_factory = sqlite3.Row
    try:
        if schema_sql:
            dest.executescript(schema_sql)
        if index_sql:
            dest.executescript(index_sql)

        placeholders = ", ".join(["?"] * len(email_columns))
        email_rows = src.execute(
            f"""
            SELECT {', '.join(email_columns)}
            FROM emails
            WHERE id BETWEEN ? AND ?
            ORDER BY id
            """,
            (min_id, max_id),
        ).fetchall()
        dest.executemany(
            f"INSERT INTO emails ({', '.join(email_columns)}) VALUES ({placeholders})",
            ([row[column] for column in email_columns] for row in email_rows),
        )

        record_placeholders = ", ".join(["?"] * len(email_record_columns))
        record_rows = src.execute(
            f"""
            SELECT {', '.join(email_record_columns)}
            FROM email_records
            WHERE email_id BETWEEN ? AND ?
            ORDER BY id
            """,
            (min_id, max_id),
        ).fetchall()
        dest.executemany(
            f"INSERT INTO email_records ({', '.join(email_record_columns)}) VALUES ({record_placeholders})",
            ([row[column] for column in email_record_columns] for row in record_rows),
        )

        metadata_rows = src.execute(
            "SELECT key, value FROM metadata"
        ).fetchall()
        dest.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ((row["key"], row["value"]) for row in metadata_rows),
        )
        dest.commit()
    finally:
        dest.close()


def split_database(source: Path, dest_dir: Path, rows_per_shard: int, overwrite: bool) -> None:
    if not source.exists():
        raise SystemExit(f"Source database not found: {source}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = list(dest_dir.glob(f"{SHARD_FILENAME_PREFIX}*{SHARD_FILENAME_SUFFIX}"))
    if existing and not overwrite:
        raise SystemExit(
            f"Destination {dest_dir} already contains shard files. Use --overwrite to replace them."
        )

    src = sqlite3.connect(source)
    src.row_factory = sqlite3.Row
    try:
        schema_sql, index_sql = fetch_schema(src)
        email_columns = table_columns(src, "emails")
        email_record_columns = table_columns(src, "email_records")
        ranges = list(chunk_ranges(src, rows_per_shard))
        if not ranges:
            raise SystemExit("No rows found in source database.")

        print(f"Splitting {source} into {len(ranges)} shard(s) in {dest_dir}")
        for chunk_index, min_id, max_id in ranges:
            shard_path = dest_dir / f"{SHARD_FILENAME_PREFIX}{chunk_index:03d}{SHARD_FILENAME_SUFFIX}"
            print(f"  -> shard {chunk_index:03d}: ids {min_id}–{max_id} -> {shard_path.name}")
            copy_chunk(
                src,
                shard_path,
                schema_sql,
                index_sql,
                email_columns,
                email_record_columns,
                chunk_index,
                min_id,
                max_id,
            )
    finally:
        src.close()


def main() -> None:
    args = parse_args()
    split_database(args.source, args.dest_dir, args.rows_per_shard, args.overwrite)


if __name__ == "__main__":
    main()
