import pytest

from app.ledger.models import GENESIS_HASH, ExecutionRecord
from app.ledger.storage import ExecutionLedger


@pytest.fixture
def ledger(tmp_path):
    return ExecutionLedger(tmp_path / "test_ledger.db")


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


def test_database_initialization(ledger):
    assert ledger.get_all() == []
    assert ledger.get_latest_hash() == GENESIS_HASH


def test_append_and_retrieve_record(ledger):
    record = create_record()

    ledger.append(record)

    records = ledger.get_all()

    assert len(records) == 1
    assert records[0] == record
    assert ledger.get_latest_hash() == record.record_hash


def test_append_chained_records(ledger):
    first = create_record()
    ledger.append(first)

    second = create_record(
        previous_hash=first.record_hash,
        code="print(2)",
    )
    ledger.append(second)

    records = ledger.get_all()

    assert len(records) == 2
    assert records[0].previous_hash == GENESIS_HASH
    assert records[1].previous_hash == first.record_hash
    assert ledger.get_latest_hash() == second.record_hash


def test_reject_invalid_previous_hash(ledger):
    record = create_record(previous_hash="invalid")

    with pytest.raises(ValueError, match="current ledger head"):
        ledger.append(record)

    assert ledger.get_all() == []


def test_get_record_by_execution_id(ledger):
    record = create_record()
    ledger.append(record)

    retrieved = ledger.get_by_execution_id(record.execution_id)

    assert retrieved == record


def test_missing_execution_id_returns_none(ledger):
    assert ledger.get_by_execution_id("missing") is None


def test_reject_duplicate_execution_id(ledger):
    record = create_record()
    ledger.append(record)

    second = ExecutionRecord.create(
        status="failed",
        exit_code=1,
        duration_ms=50,
        code="print(2)",
        stdout="",
        stderr="error",
        previous_hash=record.record_hash,
    )

    from dataclasses import replace

    duplicate = replace(second, execution_id=record.execution_id)

    with pytest.raises(Exception):
        ledger.append(duplicate)

    assert len(ledger.get_all()) == 1
