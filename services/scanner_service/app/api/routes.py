import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    ExplanationRequest,
    ExplanationResponse,
    ScanRequest,
    ScanResponse,
)
from app.scanners.llm_explainer import LLMExplainer
from app.scanners.scanner_orchestrator import ScannerOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan_code(request: ScanRequest) -> ScanResponse:
    """
    Scan code for security vulnerabilities.

    This endpoint:
    1. Accepts code content or file path
    2. Runs specified scanners (Bandit, Semgrep)
    3. Returns unified scan findings with severity levels
    4. Optionally generates LLM-based explanations

    Args:
        request: ScanRequest with code/file_path and scanner options

    Returns:
        ScanResponse with findings and statistics
    """
    # Validate request
    if not request.code and not request.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'code' or 'file_path' must be provided",
        )

    if request.code and request.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either 'code' or 'file_path', not both",
        )

    try:
        orchestrator = ScannerOrchestrator()

        # Scan code or file
        if request.code:
            response = orchestrator.scan_code(
                code=request.code,
                scanners=request.scanners,
                language=request.language,
            )
        else:
            # Validate file path exists
            file_path = Path(request.file_path)
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_path}",
                )

            response = orchestrator.scan_file(
                file_path=request.file_path,
                scanners=request.scanners,
                language=request.language,
            )

        logger.info(
            f"Scan completed: {response.total_findings} findings "
            f"in {response.scan_duration_seconds}s"
        )

        # Add LLM explanations if requested
        if request.include_explanations and response.findings:
            try:
                explainer = LLMExplainer()
                explanations = await explainer.explain_findings_batch(
                    response.findings,
                    code_context=request.code,
                )
                logger.info(f"Generated {len(explanations)} explanations")
            except Exception as e:
                logger.warning(f"Failed to generate explanations: {e}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.get("/scanners")
async def list_scanners():
    """
    List available security scanners.

    Returns information about supported scanners and their capabilities.
    """
    return {
        "available_scanners": [
            {
                "name": "bandit",
                "description": "Python-specific security linter",
                "languages": ["python"],
                "capabilities": ["security", "code-quality"],
            },
            {
                "name": "semgrep",
                "description": "Multi-language static analysis tool",
                "languages": ["python", "javascript", "typescript", "java", "go", "ruby"],
                "capabilities": ["security", "bugs", "code-quality"],
            },
        ],
        "default_scanners": ["bandit", "semgrep"],
    }


@router.get("/severity-levels")
async def list_severity_levels():
    """
    List available severity levels and their meanings.
    """
    return {
        "severity_levels": [
            {
                "level": "LOW",
                "description": "Minor issues that may not pose immediate risk",
            },
            {
                "level": "MEDIUM",
                "description": "Moderate security concerns that should be addressed",
            },
            {
                "level": "HIGH",
                "description": "Serious vulnerabilities requiring prompt attention",
            },
            {
                "level": "CRITICAL",
                "description": "Critical security flaws requiring immediate action",
            },
        ]
    }


@router.post("/explain", response_model=ExplanationResponse)
async def explain_finding(request: ExplanationRequest) -> ExplanationResponse:
    """
    Generate LLM-based explanation and remediation advice for a security finding.

    This endpoint:
    1. Takes a ScanFinding as input
    2. Uses Ollama to generate plain-English explanation
    3. Provides step-by-step remediation instructions
    4. Explains severity rationale
    5. Returns relevant security references

    Args:
        request: ExplanationRequest with finding and optional code context

    Returns:
        ExplanationResponse with detailed explanation
    """
    try:
        explainer = LLMExplainer()
        explanation = explainer.explain_finding(
            finding=request.finding,
            code_context=request.code_context,
        )

        logger.info(f"Generated explanation for {request.finding.rule_id}")
        return explanation

    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}",
        )
