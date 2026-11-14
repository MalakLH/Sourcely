from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.ledger.integrity import verify_ledger
from app.ledger.models import GENESIS_HASH
from app.ledger.storage import ExecutionLedger
from app.sandbox.executor import SandboxExecutor
from app.schemas.request import ExecutionRequest


@pytest.fixture
def ledger(tmp_path):
    return ExecutionLedger(tmp_path / "executor_test.db")


@pytest.fixture
def executor(ledger):
    instance = SandboxExecutor(ledger=ledger)
    instance.container_manager = Mock()
    instance.container_manager.execute.return_value = Mock(
        status="success",
        stdout="2\n",
        stderr="",
        exit_code=0,
        duration_ms=150.5,
        container_id="test123",
    )
    return instance


def test_successful_execution_is_recorded(executor, ledger):
    request = ExecutionRequest(
        code="print(1 + 1)",
        timeout=5,
    )

    response = executor.execute(request)

    assert response.status == "success"

    records = ledger.get_all()

    assert len(records) == 1
    assert records[0].status == "success"
    assert records[0].code_hash
    assert records[0].output_hash


def test_execution_failure_is_recorded(executor, ledger):
    executor.container_manager.execute.return_value = Mock(
        status="failed",
        stdout="",
        stderr="NameError",
        exit_code=1,
        duration_ms=100,
        container_id="test456",
    )

    request = ExecutionRequest(
        code="invalid_code",
        timeout=5,
    )

    response = executor.execute(request)

    assert response.status == "failed"
    assert len(ledger.get_all()) == 1
    assert ledger.get_all()[0].status == "failed"


def test_timeout_is_recorded(executor, ledger):
    executor.container_manager.execute.return_value = Mock(
        status="timeout",
        stdout="",
        stderr="",
        exit_code=-1,
        duration_ms=5000,
        container_id="test789",
    )

    request = ExecutionRequest(
        code="import time; time.sleep(10)",
        timeout=5,
    )

    response = executor.execute(request)

    assert response.status == "timeout"
    assert len(ledger.get_all()) == 1


def test_recorded_executions_form_valid_chain(executor, ledger):
    for code in ["print(1)", "print(2)", "print(3)"]:
        executor.execute(ExecutionRequest(code=code, timeout=5))

    report = verify_ledger(ledger)

    assert report.valid is True
    assert report.records_checked == 3


def test_invalid_request_is_not_recorded(executor, ledger):

    with pytest.raises(ValidationError):
        ExecutionRequest(
            code="print(1)",
            timeout=11,
        )

    assert ledger.get_all() == []
    executor.container_manager.execute.assert_not_called()


def test_first_record_uses_genesis_hash(executor, ledger):
    executor.execute(ExecutionRequest(code="print(1)", timeout=5))

    record = ledger.get_all()[0]

    assert record.previous_hash == GENESIS_HASH
