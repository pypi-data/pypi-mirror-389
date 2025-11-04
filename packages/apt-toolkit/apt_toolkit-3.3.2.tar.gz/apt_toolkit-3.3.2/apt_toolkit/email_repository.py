"""
Utilities for working with the validated email database bundled with the toolkit.
"""

from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "emails" / "unique_emails.db"
DEFAULT_SHARDS_DIR = DEFAULT_DB_PATH.parent / "shards"
SHARD_FILENAME_PREFIX = "unique_emails_"
SHARD_FILENAME_SUFFIX = ".db"


class EmailRepositoryError(RuntimeError):
    """Raised when the email repository cannot satisfy a request."""


def _fetch_schema(conn: sqlite3.Connection) -> Tuple[str, str]:
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


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    """Return ordered columns for `table`."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row["name"] for row in rows]


def open_email_database(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Return a sqlite3 connection for the deduplicated email dataset.

    This helper transparently supports both the legacy single-database layout
    as well as the sharded distribution introduced to keep files under the
    100 MB GitHub limit.
    """

    def _normalise_candidates(path: Path) -> List[Path]:
        """Generate absolute candidate paths to probe."""
        if path.is_absolute():
            return [path]

        candidates = [
            (BASE_DIR / path).resolve(),
            (Path.cwd() / path).resolve(),
        ]
        # Avoid duplicates while preserving order.
        seen = set()
        unique: List[Path] = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique.append(candidate)
        return unique

    def _discover_shards(path: Path) -> Sequence[Path]:
        """Return a sorted list of shard files co-located with `path`."""
        candidate_dirs = []
        if path.is_dir():
            candidate_dirs.append(path)
        else:
            candidate_dirs.extend(
                [
                    path.parent / "shards",
                    path.parent / "unique_emails_shards",
                    DEFAULT_SHARDS_DIR,
                ]
            )

        for directory in candidate_dirs:
            if not directory.exists() or not directory.is_dir():
                continue
            shards = sorted(
                p for p in directory.iterdir() if p.name.startswith(SHARD_FILENAME_PREFIX) and p.name.endswith(SHARD_FILENAME_SUFFIX)
        )
            if shards:
                return shards
        return []

    def _materialise_shards(destination: Path, shards: Sequence[Path]) -> Path:
        """
        Combine shard files into a single SQLite database at `destination`.

        The resulting file is equivalent to the original monolithic database and
        is created lazily on demand. Subsequent runs reuse the existing file.
        """
        if destination.exists():
            return destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_suffix(destination.suffix + ".partial")
        if temp_path.exists():
            temp_path.unlink()

        schema_sql = ""
        index_sql = ""
        email_columns: List[str] = []
        email_record_columns: List[str] = []
        metadata_rows: Optional[List[sqlite3.Row]] = None

        with sqlite3.connect(temp_path) as dest:
            dest.row_factory = sqlite3.Row
            dest.executescript(
                """
                PRAGMA journal_mode=OFF;
                PRAGMA synchronous=OFF;
                PRAGMA temp_store=MEMORY;
                PRAGMA foreign_keys=ON;
                """
            )

            first_shard = True
            for shard_path in shards:
                with sqlite3.connect(shard_path) as shard:
                    shard.row_factory = sqlite3.Row
                    if first_shard:
                        schema_sql, index_sql = _fetch_schema(shard)
                        if schema_sql:
                            dest.executescript(schema_sql)
                        if index_sql:
                            dest.executescript(index_sql)
                        email_columns = _table_columns(shard, "emails")
                        email_record_columns = _table_columns(shard, "email_records")
                        metadata_rows = shard.execute(
                            "SELECT key, value FROM metadata"
                        ).fetchall()
                        first_shard = False

                    email_rows = shard.execute(
                        f"SELECT {', '.join(email_columns)} FROM emails ORDER BY id"
                    ).fetchall()
                    dest.executemany(
                        f"INSERT INTO emails ({', '.join(email_columns)}) VALUES ({', '.join('?' for _ in email_columns)})",
                        ([row[column] for column in email_columns] for row in email_rows),
                    )

                    record_rows = shard.execute(
                        f"SELECT {', '.join(email_record_columns)} FROM email_records ORDER BY id"
                    ).fetchall()
                    dest.executemany(
                        f"INSERT INTO email_records ({', '.join(email_record_columns)}) VALUES ({', '.join('?' for _ in email_record_columns)})",
                        ([row[column] for column in email_record_columns] for row in record_rows),
                    )

            if metadata_rows:
                dest.executemany(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    ((row["key"], row["value"]) for row in metadata_rows),
                )
            dest.commit()

        temp_path.replace(destination)
        return destination

    target = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    candidates = _normalise_candidates(target)
    errors: List[str] = []

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            conn = sqlite3.connect(candidate)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON;")
            return conn

        shards = _discover_shards(candidate)
        if shards:
            try:
                hydrated = _materialise_shards(
                    candidate if candidate.suffix else DEFAULT_DB_PATH, shards
                )
            except OSError as exc:
                errors.append(f"{candidate} ({exc})")
                continue
            conn = sqlite3.connect(hydrated)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON;")
            return conn
        errors.append(str(candidate))

    raise EmailRepositoryError(
        "Email database not found. Checked: " + ", ".join(errors)
    )


def _row_to_dict(row: sqlite3.Row) -> Dict[str, object]:
    """Convert an sqlite Row into a plain dictionary."""
    return {key: row[key] for key in row.keys()}


class EmailRepository:
    """Read-only helper for the deduplicated email dataset."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._conn = open_email_database(self.db_path)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "EmailRepository":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, object]:
        """Return aggregate statistics about the dataset."""
        cursor = self._conn.execute("SELECT COUNT(*) AS total FROM emails")
        total = cursor.fetchone()["total"]
        metadata = dict(self._conn.execute("SELECT key, value FROM metadata").fetchall())
        return {
            "total_valid_emails": total,
            "metadata": metadata,
        }

    def count(self) -> int:
        """Return the number of deduplicated email addresses."""
        cursor = self._conn.execute("SELECT COUNT(*) FROM emails")
        return int(cursor.fetchone()[0])

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def random_email(self, domain: Optional[str] = None) -> Optional[Dict[str, object]]:
        """Return a random email entry, optionally constrained to a domain."""
        if domain:
            domain = domain.lower().lstrip("@")
            query = "SELECT * FROM emails WHERE domain = ? ORDER BY RANDOM() LIMIT 1"
            params = (domain,)
        else:
            query = "SELECT * FROM emails ORDER BY RANDOM() LIMIT 1"
            params = ()

        row = self._conn.execute(query, params).fetchone()
        if not row:
            return None
        return self._hydrate_email(row)

    def sample_by_domain(self, domain: str, limit: int = 10) -> List[Dict[str, object]]:
        """Return up to `limit` entries for the given domain."""
        domain = domain.lower().lstrip("@")
        cursor = self._conn.execute(
            """
            SELECT * FROM emails
            WHERE domain = ?
            ORDER BY (confidence_score IS NULL), confidence_score DESC, total_records DESC
            LIMIT ?
            """,
            (domain, limit),
        )
        return [self._hydrate_email(row) for row in cursor.fetchall()]

    def search(self, term: str, limit: int = 20) -> List[Dict[str, object]]:
        """Substring search across email, domain, organization, and names."""
        term_like = f"%{term.lower()}%"
        cursor = self._conn.execute(
            """
            SELECT * FROM emails
            WHERE lower(email) LIKE ?
               OR lower(domain) LIKE ?
               OR lower(organization) LIKE ?
               OR lower(first_name || ' ' || last_name) LIKE ?
            LIMIT ?
            """,
            (term_like, term_like, term_like, term_like, limit),
        )
        return [self._hydrate_email(row) for row in cursor.fetchall()]

    def emails_by_organization(self, organization: str) -> List[Dict[str, object]]:
        """Return every email entry that matches the exact organization."""
        org = organization.strip().lower()
        cursor = self._conn.execute(
            """
            SELECT * FROM emails
            WHERE lower(organization) = ?
            ORDER BY email
            """,
            (org,),
        )
        return [self._hydrate_email(row) for row in cursor.fetchall()]

    def records_for_email(self, email: str) -> List[Dict[str, object]]:
        """Return all original CSV records for a specific email address."""
        email = email.lower()
        cursor = self._conn.execute("SELECT id FROM emails WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise EmailRepositoryError(f"No email found for address: {email}")

        email_id = row["id"]
        record_cursor = self._conn.execute(
            """
            SELECT source_file, source_row, raw_record
            FROM email_records
            WHERE email_id = ?
            ORDER BY source_file, source_row
            """,
            (email_id,),
        )
        return [
            {
                "source_file": record["source_file"],
                "source_row": record["source_row"],
                "raw_record": json.loads(record["raw_record"]),
            }
            for record in record_cursor.fetchall()
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _hydrate_email(self, row: sqlite3.Row) -> Dict[str, object]:
        """Attach a representative raw record for context."""
        result = _row_to_dict(row)
        result["email"] = result["email"].lower()

        record_row = self._conn.execute(
            """
            SELECT raw_record
            FROM email_records
            WHERE email_id = ?
            ORDER BY source_file, source_row
            LIMIT 1
            """,
            (row["id"],),
        ).fetchone()
        if record_row:
            result["sample_record"] = json.loads(record_row["raw_record"])
        else:
            result["sample_record"] = {}
        return result
