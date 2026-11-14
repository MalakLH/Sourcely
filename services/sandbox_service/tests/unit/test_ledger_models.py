
from dataclasses import replace

from app.ledger.models import (
    GENESIS_HASH,
    ExecutionRecord,
    calculate_record_hash,
)


def create_record(previous_hash=GENESIS_HASH):
    return ExecutionRecord.create(
        status="success",
        exit_code=0,
        duration_ms=120.456,
        code="print(1 + 1)",
        stdout="2\n",
        stderr="",
        previous_hash=previous_hash,
    )


def test_record_creation():
    record = create_record()

    assert record.execution_id
    assert record.timestamp
    assert record.status == "success"
    assert record.exit_code == 0
    assert record.duration_ms == 120.456
    assert len(record.code_hash) == 64
    assert len(record.output_hash) == 64
    assert len(record.record_hash) == 64
    assert record.previous_hash == GENESIS_HASH


def test_code_hash_is_deterministic():
    first = create_record()
    second = create_record()

    assert first.code_hash == second.code_hash


def test_output_hash_changes_when_output_changes():
    first = create_record()

    second = ExecutionRecord.create(
        status="success",
        exit_code=0,
        duration_ms=120,
        code="print(1 + 1)",
        stdout="different output",
        stderr="",
        previous_hash=GENESIS_HASH,
    )

    assert first.output_hash != second.output_hash


def test_record_hash_is_deterministic_for_same_record():
    record = create_record()

    assert calculate_record_hash(record) == record.record_hash


def test_record_hash_detects_metadata_modification():
    record = create_record()

    modified = replace(record, status="failed")

    assert calculate_record_hash(modified) != record.record_hash
