from dataclasses import replace

from app.ledger.integrity import verify_ledger, verify_records
from app.ledger.models import GENESIS_HASH, ExecutionRecord
from app.ledger.storage import ExecutionLedger


def create_record(previous_hash=GENESIS_HASH, code="print(1)"):
    return ExecutionRecord.create(
        status="success",
        exit_code=0,
        duration_ms=100,
        code=code,
        stdout="1\n",
        stderr="",
        previous_hash=previous_hash,
    )


def test_empty_chain_is_valid():
    report = verify_records([])

    assert report.valid is True
    assert report.records_checked == 0


def test_single_record_chain_is_valid():
    record = create_record()

    report = verify_records([record])

    assert report.valid is True
    assert report.records_checked == 1


def test_multiple_records_chain_is_valid():
    first = create_record()

    second = create_record(
        previous_hash=first.record_hash,
        code="print(2)",
    )

    report = verify_records([first, second])

    assert report.valid is True
    assert report.records_checked == 2


def test_detect_modified_record():
    record = create_record()

    modified = replace(record, status="failed")

    report = verify_records([modified])

    assert report.valid is False
    assert report.invalid_record_id == record.execution_id
    assert report.reason == "Record hash does not match its contents."


def test_detect_broken_chain():
    first = create_record()
    second = create_record(previous_hash="f" * 64)

    report = verify_records([first, second])

    assert report.valid is False
    assert report.invalid_record_id == second.execution_id
    assert report.reason == ("Previous hash does not match the preceding record.")


def test_detect_duplicate_execution_ids():
    first = create_record()
    second = create_record(previous_hash=first.record_hash)

    duplicate = replace(second, execution_id=first.execution_id)

    report = verify_records([first, duplicate])

    assert report.valid is False
    assert report.reason == "Duplicate execution ID."


def test_verify_persisted_ledger(tmp_path):
    ledger = ExecutionLedger(tmp_path / "ledger.db")

    first = create_record()
    ledger.append(first)

    second = create_record(previous_hash=first.record_hash)
    ledger.append(second)

    report = verify_ledger(ledger)

    assert report.valid is True
    assert report.records_checked == 2
