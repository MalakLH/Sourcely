import json
import sqlite3
from pathlib import Path

from app.ledger.models import ExecutionRecord


class ExecutionLedger:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)

        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_records (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    duration_ms REAL NOT NULL,
                    code_hash TEXT NOT NULL,
                    output_hash TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL
                )
                """
            )

    def append(self, record: ExecutionRecord) -> ExecutionRecord:
        """
        Append a record atomically.

        The previous hash is checked inside the write transaction so
        concurrent writers cannot append records against the same parent.
        """
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            row = connection.execute(
                """
                SELECT record_hash
                FROM execution_records
                ORDER BY sequence DESC
                LIMIT 1
                """
            ).fetchone()

            expected_previous_hash = row["record_hash"] if row else "0" * 64

            if record.previous_hash != expected_previous_hash:
                raise ValueError("Record does not reference the current ledger head.")

            connection.execute(
                """
                INSERT INTO execution_records (
                    execution_id,
                    timestamp,
                    status,
                    exit_code,
                    duration_ms,
                    code_hash,
                    output_hash,
                    previous_hash,
                    record_hash,
                    record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.execution_id,
                    record.timestamp,
                    record.status,
                    record.exit_code,
                    record.duration_ms,
                    record.code_hash,
                    record.output_hash,
                    record.previous_hash,
                    record.record_hash,
                    json.dumps(
                        record.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )

            connection.commit()
            return record

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get_latest_hash(self) -> str:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_hash
                FROM execution_records
                ORDER BY sequence DESC
                LIMIT 1
                """
            ).fetchone()

            return row["record_hash"] if row else "0" * 64

    def get_all(self) -> list[ExecutionRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_json
                FROM execution_records
                ORDER BY sequence ASC
                """
            ).fetchall()

            return [ExecutionRecord(**json.loads(row["record_json"])) for row in rows]

    def get_by_execution_id(
        self,
        execution_id: str,
    ) -> ExecutionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_json
                FROM execution_records
                WHERE execution_id = ?
                """,
                (execution_id,),
            ).fetchone()

            if row is None:
                return None

            return ExecutionRecord(**json.loads(row["record_json"]))
