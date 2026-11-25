import logging
import time

from app.models.schemas import ScanFinding, ScanResponse
from app.scanners.bandit_scanner import BanditScanner
from app.scanners.semgrep_scanner import SemgrepScanner

logger = logging.getLogger(__name__)


class ScannerOrchestrator:
    """
    Orchestrates multiple security scanners and aggregates results.
    """

    def __init__(self):
        self.bandit = BanditScanner()
        self.semgrep = SemgrepScanner()

        self.available_scanners = {
            "bandit": self.bandit,
            "semgrep": self.semgrep,
        }

    def scan_code(
        self,
        code: str,
        scanners: list[str],
        language: str | None = None,
    ) -> ScanResponse:
        """
        Scan code using specified scanners.

        Args:
            code: Code content to scan
            scanners: List of scanner names to use
            language: Programming language (optional)

        Returns:
            ScanResponse with aggregated findings
        """
        start_time = time.time()
        all_findings = []
        scanners_used = []

        for scanner_name in scanners:
            scanner = self.available_scanners.get(scanner_name.lower())

            if not scanner:
                logger.warning(f"Unknown scanner: {scanner_name}")
                continue

            try:
                logger.info(f"Running {scanner_name} scanner...")
                findings = scanner.scan_code(code, language or "python")
                all_findings.extend(findings)
                scanners_used.append(scanner_name)
                logger.info(f"{scanner_name} found {len(findings)} issues")

            except Exception as e:
                logger.error(f"Error running {scanner_name}: {e}")

        # Calculate statistics
        findings_by_severity = self._count_by_severity(all_findings)
        duration = time.time() - start_time

        return ScanResponse(
            status="success",
            findings=all_findings,
            total_findings=len(all_findings),
            findings_by_severity=findings_by_severity,
            scan_duration_seconds=round(duration, 2),
            scanners_used=scanners_used,
        )

    def scan_file(
        self,
        file_path: str,
        scanners: list[str],
        language: str | None = None,
    ) -> ScanResponse:
        """
        Scan a file using specified scanners.

        Args:
            file_path: Path to file or directory
            scanners: List of scanner names to use
            language: Programming language (optional)

        Returns:
            ScanResponse with aggregated findings
        """
        start_time = time.time()
        all_findings = []
        scanners_used = []

        for scanner_name in scanners:
            scanner = self.available_scanners.get(scanner_name.lower())

            if not scanner:
                logger.warning(f"Unknown scanner: {scanner_name}")
                continue

            try:
                logger.info(f"Running {scanner_name} scanner on {file_path}...")
                findings = scanner.scan_file(file_path)
                all_findings.extend(findings)
                scanners_used.append(scanner_name)
                logger.info(f"{scanner_name} found {len(findings)} issues")

            except Exception as e:
                logger.error(f"Error running {scanner_name}: {e}")

        # Calculate statistics
        findings_by_severity = self._count_by_severity(all_findings)
        duration = time.time() - start_time

        return ScanResponse(
            status="success",
            findings=all_findings,
            total_findings=len(all_findings),
            findings_by_severity=findings_by_severity,
            scan_duration_seconds=round(duration, 2),
            scanners_used=scanners_used,
        )

    def _count_by_severity(self, findings: list[ScanFinding]) -> dict[str, int]:
        """Count findings by severity level."""
        counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

        for finding in findings:
            severity = finding.severity.value
            counts[severity] = counts.get(severity, 0) + 1

        return counts
