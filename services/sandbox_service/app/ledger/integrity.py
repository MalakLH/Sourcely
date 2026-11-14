from dataclasses import dataclass

from app.ledger.models import (
    GENESIS_HASH,
    ExecutionRecord,
    calculate_record_hash,
)
from app.ledger.storage import ExecutionLedger


@dataclass(frozen=True)
class IntegrityReport:
    valid: bool
    records_checked: int
    invalid_record_id: str | None = None
    reason: str | None = None


def verify_records(records: list[ExecutionRecord]) -> IntegrityReport:
    """
    Verify the complete hash chain.

    Checks:
    1. The first record references the genesis hash.
    2. Every record references the preceding record's hash.
    3. Every record's own hash matches its contents.
    4. Execution IDs are unique.
    """
    previous_hash = GENESIS_HASH
    seen_ids: set[str] = set()

    for index, record in enumerate(records):
        if record.execution_id in seen_ids:
            return IntegrityReport(
                valid=False,
                records_checked=index,
                invalid_record_id=record.execution_id,
                reason="Duplicate execution ID.",
            )

        seen_ids.add(record.execution_id)

        if record.previous_hash != previous_hash:
            return IntegrityReport(
                valid=False,
                records_checked=index,
                invalid_record_id=record.execution_id,
                reason="Previous hash does not match the preceding record.",
            )

        expected_hash = calculate_record_hash(record)

        if record.record_hash != expected_hash:
            return IntegrityReport(
                valid=False,
                records_checked=index,
                invalid_record_id=record.execution_id,
                reason="Record hash does not match its contents.",
            )

        previous_hash = record.record_hash

    return IntegrityReport(
        valid=True,
        records_checked=len(records),
    )


def verify_ledger(ledger: ExecutionLedger) -> IntegrityReport:
    """Retrieve and verify all records in a ledger."""
    try:
        records = ledger.get_all()
    except Exception:
        return IntegrityReport(
            valid=False,
            records_checked=0,
            reason="Unable to retrieve ledger records.",
        )

    return verify_records(records)
