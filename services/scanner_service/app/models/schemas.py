from enum import StrEnum

from pydantic import BaseModel, Field


class SeverityLevel(StrEnum):
    """Severity levels for security findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScanFinding(BaseModel):
    """Unified schema for scanner findings."""

    file: str = Field(..., description="File path where the issue was found")
    line: int = Field(..., description="Line number of the issue")
    column: int | None = Field(None, description="Column number (if available)")
    rule_id: str = Field(..., description="Scanner rule identifier")
    severity: SeverityLevel = Field(..., description="Severity level of the finding")
    description: str = Field(..., description="Description of the security issue")
    scanner: str = Field(..., description="Scanner that detected this issue (bandit/semgrep)")
    code_snippet: str | None = Field(None, description="Code snippet showing the issue")
    cwe_id: str | None = Field(None, description="CWE identifier if available")
    confidence: str | None = Field(None, description="Confidence level of the finding")
    fix_suggestion: str | None = Field(None, description="Suggested fix (if available)")


class ScanRequest(BaseModel):
    """Request schema for code scanning."""

    code: str | None = Field(None, description="Code content to scan (for inline scanning)")
    file_path: str | None = Field(
        None, description="Path to file or directory to scan (for file-based scanning)"
    )
    language: str | None = Field(
        None, description="Programming language (python, javascript, etc.)"
    )
    scanners: list[str] = Field(
        default=["bandit", "semgrep"], description="List of scanners to run"
    )
    include_explanations: bool = Field(
        default=False, description="Generate LLM-based explanations for findings"
    )


class ScanResponse(BaseModel):
    """Response schema for code scanning."""

    status: str = Field(..., description="Scan status (success/error)")
    findings: list[ScanFinding] = Field(default_factory=list, description="List of findings")
    total_findings: int = Field(..., description="Total number of findings")
    findings_by_severity: dict[str, int] = Field(
        default_factory=dict, description="Count of findings by severity"
    )
    scan_duration_seconds: float = Field(..., description="Time taken to complete scan")
    scanners_used: list[str] = Field(default_factory=list, description="Scanners that were run")


class ExplanationRequest(BaseModel):
    """Request schema for LLM-based explanation of a finding."""

    finding: ScanFinding = Field(..., description="The finding to explain")
    code_context: str | None = Field(None, description="Additional code context around the finding")


class ExplanationResponse(BaseModel):
    """Response schema for LLM explanation."""

    finding_id: str = Field(..., description="Identifier for the finding")
    explanation: str = Field(..., description="Plain-English explanation of the vulnerability")
    remediation: str = Field(..., description="Recommended remediation steps")
    severity_rationale: str = Field(..., description="Why this severity level was assigned")
    references: list[str] = Field(
        default_factory=list, description="Relevant security references (CWE, OWASP, etc.)"
    )
