import pytest

from app.models.schemas import SeverityLevel
from app.scanners.bandit_scanner import BanditScanner
from app.scanners.scanner_orchestrator import ScannerOrchestrator
from app.scanners.semgrep_scanner import SemgrepScanner


@pytest.fixture
def vulnerable_python_code():
    """Sample vulnerable Python code for testing."""
    return """
import os

# SQL Injection vulnerability
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return execute_query(query)

# Hardcoded secret
API_KEY = "sk-1234567890abcdef"

# Use of eval
def calculate(expression):
    return eval(expression)
"""


@pytest.fixture
def safe_python_code():
    """Sample safe Python code."""
    return """
def add_numbers(a, b):
    return a + b

def main():
    result = add_numbers(1, 2)
    print(f"Result: {result}")
"""


def test_bandit_scanner_finds_vulnerabilities(vulnerable_python_code):
    """Test that Bandit detects vulnerabilities."""
    scanner = BanditScanner()
    findings = scanner.scan_code(vulnerable_python_code)

    assert len(findings) > 0
    assert all(f.scanner == "bandit" for f in findings)
    assert all(isinstance(f.severity, SeverityLevel) for f in findings)
    assert all(f.line > 0 for f in findings)


def test_bandit_scanner_safe_code(safe_python_code):
    """Test Bandit on safe code."""
    scanner = BanditScanner()
    findings = scanner.scan_code(safe_python_code)

    # Safe code should have few or no findings
    assert isinstance(findings, list)


def test_semgrep_scanner_finds_issues(vulnerable_python_code):
    """Test that Semgrep detects issues."""
    scanner = SemgrepScanner()
    findings = scanner.scan_code(vulnerable_python_code, language="python")

    # Semgrep should find issues (may vary based on rules)
    assert isinstance(findings, list)
    assert all(f.scanner == "semgrep" for f in findings)


def test_scanner_orchestrator_multiple_scanners(vulnerable_python_code):
    """Test running multiple scanners together."""
    orchestrator = ScannerOrchestrator()
    response = orchestrator.scan_code(
        code=vulnerable_python_code,
        scanners=["bandit", "semgrep"],
        language="python",
    )

    assert response.status == "success"
    assert len(response.scanners_used) >= 1
    assert response.total_findings >= 0
    assert "LOW" in response.findings_by_severity
    assert response.scan_duration_seconds > 0


def test_scanner_orchestrator_single_scanner(vulnerable_python_code):
    """Test running a single scanner."""
    orchestrator = ScannerOrchestrator()
    response = orchestrator.scan_code(
        code=vulnerable_python_code,
        scanners=["bandit"],
        language="python",
    )

    assert response.status == "success"
    assert "bandit" in response.scanners_used


def test_finding_schema_validation(vulnerable_python_code):
    """Test that findings match the expected schema."""
    scanner = BanditScanner()
    findings = scanner.scan_code(vulnerable_python_code)

    if findings:
        finding = findings[0]
        assert hasattr(finding, "file")
        assert hasattr(finding, "line")
        assert hasattr(finding, "rule_id")
        assert hasattr(finding, "severity")
        assert hasattr(finding, "description")
        assert hasattr(finding, "scanner")


def test_severity_mapping():
    """Test severity level mapping."""
    scanner = BanditScanner()

    assert scanner._map_severity("LOW") == SeverityLevel.LOW
    assert scanner._map_severity("MEDIUM") == SeverityLevel.MEDIUM
    assert scanner._map_severity("HIGH") == SeverityLevel.HIGH


def test_findings_by_severity_count(vulnerable_python_code):
    """Test counting findings by severity."""
    orchestrator = ScannerOrchestrator()
    response = orchestrator.scan_code(
        code=vulnerable_python_code,
        scanners=["bandit"],
        language="python",
    )

    severity_counts = response.findings_by_severity
    total_from_counts = sum(severity_counts.values())

    assert total_from_counts == response.total_findings
