import logging
from typing import Optional

from langchain_ollama import ChatOllama

from app.core.config import settings
from app.models.schemas import ExplanationResponse, ScanFinding

logger = logging.getLogger(__name__)


class LLMExplainer:
    """
    Generates plain-English explanations and remediation advice for security findings
    using an LLM (Ollama).
    """

    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature,
            timeout=120.0,  # 120 second timeout for LLM calls
            num_predict=512,  # Cap output tokens to 512 for faster responses
        )

    def explain_finding(
        self,
        finding: ScanFinding,
        code_context: Optional[str] = None,
    ) -> ExplanationResponse:
        """
        Generate a detailed explanation for a security finding.

        Args:
            finding: The ScanFinding to explain
            code_context: Additional code context (optional)

        Returns:
            ExplanationResponse with explanation and remediation
        """
        # Build context from finding
        context_parts = [
            f"Scanner: {finding.scanner}",
            f"Rule ID: {finding.rule_id}",
            f"Severity: {finding.severity.value}",
            f"Description: {finding.description}",
            f"File: {finding.file}",
            f"Line: {finding.line}",
        ]

        if finding.cwe_id:
            context_parts.append(f"CWE: {finding.cwe_id}")

        if finding.code_snippet:
            context_parts.append(f"\nCode:\n```\n{finding.code_snippet}\n```")

        if code_context:
            context_parts.append(f"\nAdditional Context:\n```\n{code_context}\n```")

        context = "\n".join(context_parts)

        # Create concise prompt for LLM (optimized for fast response)
        prompt = f"""Analyze this security finding and provide a brief response in JSON format:

{context}

Provide a concise response with:
1. What: Brief explanation (2-3 sentences)
2. Fix: Quick remediation steps (bullet points)
3. Why {finding.severity.value}: One sentence justification

Keep response under 400 words. Be direct and actionable.

Response:"""

        try:
            # Generate explanation using LLM
            response = self.llm.invoke(prompt)
            explanation_text = response.content.strip()

            # Parse the response
            parsed = self._parse_llm_response(explanation_text)

            return ExplanationResponse(
                finding_id=f"{finding.scanner}-{finding.rule_id}-{finding.line}",
                explanation=parsed["explanation"],
                remediation=parsed["remediation"],
                severity_rationale=parsed["severity_rationale"],
                references=parsed["references"],
            )

        except Exception as e:
            logger.error(f"Error generating LLM explanation: {e}")
            # Return a basic fallback explanation
            return self._fallback_explanation(finding)

    def _parse_llm_response(self, response: str) -> dict:
        """Parse structured response from LLM."""
        sections = {
            "explanation": "",
            "remediation": "",
            "severity_rationale": "",
            "references": [],
        }

        # Split by section headers
        lines = response.split("\n")
        current_section = None

        for line in lines:
            line_upper = line.strip().upper()

            if "EXPLANATION:" in line_upper:
                current_section = "explanation"
            elif "REMEDIATION:" in line_upper:
                current_section = "remediation"
            elif "SEVERITY RATIONALE:" in line_upper or "SEVERITY:" in line_upper:
                current_section = "severity_rationale"
            elif "REFERENCES:" in line_upper:
                current_section = "references"
            elif current_section and line.strip():
                if current_section == "references":
                    # Parse references as list items
                    if line.strip().startswith(("-", "*", "•")):
                        ref = line.strip().lstrip("-*•").strip()
                        if ref:
                            sections["references"].append(ref)
                    elif line.strip():
                        sections["references"].append(line.strip())
                else:
                    sections[current_section] += line + "\n"

        # Clean up sections
        for key in ["explanation", "remediation", "severity_rationale"]:
            sections[key] = sections[key].strip()

        # If parsing failed, use the whole response as explanation
        if not sections["explanation"]:
            sections["explanation"] = response

        return sections

    def _fallback_explanation(self, finding: ScanFinding) -> ExplanationResponse:
        """Provide a basic fallback explanation when LLM fails."""
        explanation = (
            f"A {finding.severity.value} severity security issue was detected by {finding.scanner}. "
            f"{finding.description}"
        )

        remediation = (
            "1. Review the code at the specified location\n"
            "2. Consult the scanner documentation for this rule\n"
            "3. Apply security best practices to fix the issue\n"
            "4. Re-run the scanner to verify the fix"
        )

        severity_rationale = (
            f"This issue was classified as {finding.severity.value} severity based on "
            f"the scanner's rule configuration and potential security impact."
        )

        references = []
        if finding.cwe_id:
            references.append(f"https://cwe.mitre.org/data/definitions/{finding.cwe_id.replace('CWE-', '')}.html")
        references.append("https://owasp.org/www-project-top-ten/")

        return ExplanationResponse(
            finding_id=f"{finding.scanner}-{finding.rule_id}-{finding.line}",
            explanation=explanation,
            remediation=remediation,
            severity_rationale=severity_rationale,
            references=references,
        )

    async def explain_findings_batch(
        self,
        findings: list[ScanFinding],
        code_context: Optional[str] = None,
    ) -> list[ExplanationResponse]:
        """
        Generate explanations for multiple findings.

        Args:
            findings: List of ScanFindings
            code_context: Optional code context

        Returns:
            List of ExplanationResponses
        """
        explanations = []

        for finding in findings:
            try:
                explanation = self.explain_finding(finding, code_context)
                explanations.append(explanation)
            except Exception as e:
                logger.error(f"Error explaining finding {finding.rule_id}: {e}")
                # Add fallback
                explanations.append(self._fallback_explanation(finding))

        return explanations
