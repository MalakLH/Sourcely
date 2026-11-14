import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    timestamp: str
    status: str
    exit_code: int | None
    duration_ms: float
    code_hash: str
    output_hash: str
    previous_hash: str
    record_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        status: str,
        exit_code: int | None,
        duration_ms: float,
        code: str,
        stdout: str,
        stderr: str,
        previous_hash: str,
    ) -> "ExecutionRecord":
        record = cls(
            execution_id=str(uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            status=status,
            exit_code=exit_code,
            duration_ms=round(duration_ms, 3),
            code_hash=hashlib.sha256(code.encode("utf-8")).hexdigest(),
            output_hash=hashlib.sha256(f"{stdout}\0{stderr}".encode()).hexdigest(),
            previous_hash=previous_hash,
        )

        return cls(
            **{
                **asdict(record),
                "record_hash": calculate_record_hash(record),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_json(record: ExecutionRecord) -> str:
    """Serialize a record deterministically, excluding its own hash."""
    payload = record.to_dict()
    payload.pop("record_hash", None)

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def calculate_record_hash(record: ExecutionRecord) -> str:
    """Calculate the SHA-256 hash of the canonical record representation."""
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()
