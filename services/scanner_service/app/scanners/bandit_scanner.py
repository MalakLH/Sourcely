import json
import logging
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings
from app.models.schemas import ScanFinding, SeverityLevel

logger = logging.getLogger(__name__)


class BanditScanner:
    """
    Wrapper for Bandit security scanner.

    Executes bandit CLI and parses JSON output into unified ScanFinding schema.
    """

    def __init__(self):
        self.scanner_name = "bandit"

    def _map_severity(self, bandit_severity: str) -> SeverityLevel:
        """Map Bandit severity levels to unified severity."""
        severity_map = {
            "LOW": SeverityLevel.LOW,
            "MEDIUM": SeverityLevel.MEDIUM,
            "HIGH": SeverityLevel.HIGH,
        }
        return severity_map.get(bandit_severity.upper(), SeverityLevel.MEDIUM)

    def scan_code(self, code: str, language: str = "python") -> list[ScanFinding]:
        """
        Scan code content using Bandit.

        Args:
            code: Python code content to scan
            language: Programming language (must be python for Bandit)

        Returns:
            List of ScanFinding objects
        """
        if language and language.lower() != "python":
            logger.info(f"Bandit only supports Python, skipping for language: {language}")
            return []

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            temp_path = Path(temp_file.name)

        try:
            return self.scan_file(str(temp_path))
        finally:
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)

    def scan_file(self, file_path: str) -> list[ScanFinding]:
        """
        Scan a file or directory using Bandit.

        Args:
            file_path: Path to Python file or directory

        Returns:
            List of ScanFinding objects
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []

        # Build bandit command
        cmd = [
            "bandit",
            "-r" if path.is_dir() else "-f",
            "json",
            str(path),
        ]

        try:
            # Run bandit
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.scan_timeout_seconds,
            )

            # Bandit returns non-zero exit code when findings are detected
            # We still want to parse the results
            if result.stdout:
                return self._parse_bandit_output(result.stdout, file_path)
            else:
                logger.warning(f"No output from Bandit: {result.stderr}")
                return []

        except subprocess.TimeoutExpired:
            logger.error(f"Bandit scan timed out after {settings.scan_timeout_seconds}s")
            return []
        except FileNotFoundError:
            logger.error("Bandit not found. Please install it: pip install bandit")
            return []
        except Exception as e:
            logger.error(f"Error running Bandit: {e}")
            return []

    def _parse_bandit_output(self, output: str, scanned_path: str) -> list[ScanFinding]:
        """
        Parse Bandit JSON output into ScanFinding objects.

        Args:
            output: JSON output from Bandit
            scanned_path: Path that was scanned

        Returns:
            List of ScanFinding objects
        """
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit output: {e}")
            return []

        findings = []
        results = data.get("results", [])

        for result in results:
            # Extract code snippet
            code_snippet = result.get("code", "")
            if isinstance(code_snippet, str):
                code_snippet = code_snippet.strip()

            # Map CWE if available
            cwe_id = None
            if "issue_cwe" in result and result["issue_cwe"]:
                cwe_data = result["issue_cwe"]
                if isinstance(cwe_data, dict):
                    cwe_id = f"CWE-{cwe_data.get('id', '')}"
                elif isinstance(cwe_data, (int, str)):
                    cwe_id = f"CWE-{cwe_data}"

            finding = ScanFinding(
                file=result.get("filename", scanned_path),
                line=result.get("line_number", 0),
                column=result.get("col_offset"),
                rule_id=result.get("test_id", "unknown"),
                severity=self._map_severity(result.get("issue_severity", "MEDIUM")),
                description=result.get("issue_text", "No description available"),
                scanner=self.scanner_name,
                code_snippet=code_snippet,
                cwe_id=cwe_id,
                confidence=result.get("issue_confidence"),
            )
            findings.append(finding)

        return findings
