import json
import logging
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings
from app.models.schemas import ScanFinding, SeverityLevel

logger = logging.getLogger(__name__)


class SemgrepScanner:
    """
    Wrapper for Semgrep security scanner.

    Executes semgrep CLI and parses JSON output into unified ScanFinding schema.
    """

    def __init__(self):
        self.scanner_name = "semgrep"

    def _map_severity(self, semgrep_severity: str) -> SeverityLevel:
        """Map Semgrep severity levels to unified severity."""
        severity_map = {
            "INFO": SeverityLevel.LOW,
            "WARNING": SeverityLevel.MEDIUM,
            "ERROR": SeverityLevel.HIGH,
        }
        return severity_map.get(semgrep_severity.upper(), SeverityLevel.MEDIUM)

    def scan_code(self, code: str, language: str = "python") -> list[ScanFinding]:
        """
        Scan code content using Semgrep.

        Args:
            code: Code content to scan
            language: Programming language

        Returns:
            List of ScanFinding objects
        """
        # Determine file extension from language
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "ruby": ".rb",
        }
        extension = ext_map.get(language.lower() if language else "python", ".py")

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=extension, delete=False, encoding="utf-8"
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
        Scan a file or directory using Semgrep.

        Args:
            file_path: Path to file or directory

        Returns:
            List of ScanFinding objects
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []

        # Build semgrep command with auto config (uses registry rules)
        cmd = [
            "semgrep",
            "--config=auto",  # Use Semgrep Registry rules
            "--json",
            "--quiet",
            str(path),
        ]

        try:
            # Run semgrep
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.scan_timeout_seconds,
            )

            # Semgrep returns 0 on success, even with findings
            if result.returncode == 0 and result.stdout:
                return self._parse_semgrep_output(result.stdout, file_path)
            elif result.returncode != 0:
                logger.warning(f"Semgrep returned non-zero exit code: {result.stderr}")
                # Still try to parse output if available
                if result.stdout:
                    return self._parse_semgrep_output(result.stdout, file_path)
            return []

        except subprocess.TimeoutExpired:
            logger.error(f"Semgrep scan timed out after {settings.scan_timeout_seconds}s")
            return []
        except FileNotFoundError:
            logger.error("Semgrep not found. Please install it: pip install semgrep")
            return []
        except Exception as e:
            logger.error(f"Error running Semgrep: {e}")
            return []

    def _parse_semgrep_output(self, output: str, scanned_path: str) -> list[ScanFinding]:
        """
        Parse Semgrep JSON output into ScanFinding objects.

        Args:
            output: JSON output from Semgrep
            scanned_path: Path that was scanned

        Returns:
            List of ScanFinding objects
        """
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep output: {e}")
            return []

        findings = []
        results = data.get("results", [])

        for result in results:
            # Extract metadata
            check_id = result.get("check_id", "unknown")
            extra = result.get("extra", {})

            # Get severity
            severity_str = extra.get("severity", "WARNING")
            severity = self._map_severity(severity_str)

            # Get code snippet from matched lines
            code_snippet = None
            if "lines" in extra:
                code_snippet = extra["lines"].strip()

            # Extract CWE from metadata if available
            cwe_id = None
            metadata = extra.get("metadata", {})
            if "cwe" in metadata:
                cwe_list = metadata["cwe"]
                if isinstance(cwe_list, list) and cwe_list:
                    cwe_id = cwe_list[0]

            # Get description
            description = extra.get("message", "No description available")

            # Location information
            start = result.get("start", {})
            line = start.get("line", 0)
            column = start.get("col", 0)

            finding = ScanFinding(
                file=result.get("path", scanned_path),
                line=line,
                column=column if column > 0 else None,
                rule_id=check_id,
                severity=severity,
                description=description,
                scanner=self.scanner_name,
                code_snippet=code_snippet,
                cwe_id=cwe_id,
                confidence=None,  # Semgrep doesn't provide confidence
            )
            findings.append(finding)

        return findings
