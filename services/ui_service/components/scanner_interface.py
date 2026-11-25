"""Scanner interface component for code security analysis."""

import asyncio

import httpx
import streamlit as st
from streamlit_ace import st_ace
from utils.api_client import SourcelyAPIClient


def render_scanner_interface(api_client: SourcelyAPIClient):
    """
    Render the code scanner interface.

    Args:
        api_client: API client for backend communication
    """
    st.header("🔍 Code Security Scanner")

    st.markdown(
        """
        Paste your code below to scan for security vulnerabilities using Bandit (Python)
        and Semgrep (multi-language). Get detailed explanations and remediation advice.
        """
    )

    # Two columns: editor and settings
    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("⚙️ Settings")

        # Language selection
        language = st.selectbox(
            "Language",
            ["python", "javascript", "typescript", "java", "go", "ruby"],
            index=0,
        )

        # Scanner selection
        available_scanners = ["bandit", "semgrep"]
        selected_scanners = st.multiselect(
            "Scanners",
            available_scanners,
            default=available_scanners,
        )

        # Include explanations
        include_explanations = st.checkbox("Generate LLM Explanations", value=True)

        # Scan button
        scan_button = st.button(
            "🔍 Run Vulnerability Scan", type="primary", use_container_width=True
        )

    with col1:
        # Code editor
        st.subheader("📝 Code Editor")

        # Sample code based on language
        sample_code = {
            "python": """import os

# Security Issues:
password = "hardcoded_secret_123"  # Hardcoded password
api_key = "sk-1234567890abcdef"    # Hardcoded API key

def get_user(user_id):
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return execute_query(query)

def calculate(expression):
    # Use of eval
    return eval(expression)
""",
            "javascript": """// Security Issues:
const password = "admin123";  // Hardcoded password

function getUserData(userId) {
    // SQL Injection
    const query = "SELECT * FROM users WHERE id = '" + userId + "'";
    return db.query(query);
}

// XSS vulnerability
function displayMessage(msg) {
    document.getElementById("output").innerHTML = msg;
}
""",
        }

        # Initialize session state for code
        if "code_content" not in st.session_state:
            st.session_state.code_content = sample_code.get(
                language, "# Enter your code here"
            )

        # Code editor with syntax highlighting
        code_content = st_ace(
            value=st.session_state.code_content,
            language=language,
            theme="monokai",
            height=300,
            key="code_editor",
        )

        st.session_state.code_content = code_content

    # Scan results section
    if scan_button and code_content.strip():
        st.divider()
        st.subheader("📊 Scan Results")

        with st.spinner("Scanning code for vulnerabilities..."):
            try:
                # Run scan
                scan_result = asyncio.run(
                    api_client.scan_code(
                        code=code_content,
                        language=language,
                        scanners=selected_scanners,
                        include_explanations=include_explanations,
                    )
                )

                # Display summary
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Findings", scan_result.get("total_findings", 0))

                with col2:
                    findings_by_severity = scan_result.get("findings_by_severity", {})
                    critical_high = findings_by_severity.get(
                        "CRITICAL", 0
                    ) + findings_by_severity.get("HIGH", 0)
                    st.metric("Critical + High", critical_high)

                with col3:
                    medium = findings_by_severity.get("MEDIUM", 0)
                    st.metric("Medium", medium)

                with col4:
                    low = findings_by_severity.get("LOW", 0)
                    st.metric("Low", low)

                # Display findings
                findings = scan_result.get("findings", [])

                if not findings:
                    st.success("✅ No security issues found!")
                else:
                    # Group findings by severity
                    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                    findings_by_sev = {}

                    for finding in findings:
                        sev = finding.get("severity", "UNKNOWN")
                        if sev not in findings_by_sev:
                            findings_by_sev[sev] = []
                        findings_by_sev[sev].append(finding)

                    # Display findings by severity
                    for severity in severity_order:
                        if severity not in findings_by_sev:
                            continue

                        sev_findings = findings_by_sev[severity]

                        # Severity header with color
                        severity_colors = {
                            "CRITICAL": "🔴",
                            "HIGH": "🟠",
                            "MEDIUM": "🟡",
                            "LOW": "🟢",
                        }
                        emoji = severity_colors.get(severity, "⚪")

                        st.markdown(
                            f"### {emoji} {severity} ({len(sev_findings)} findings)"
                        )

                        # Display each finding
                        for idx, finding in enumerate(sev_findings, 1):
                            with st.expander(
                                f"{idx}. {finding.get('rule_id', 'Unknown')} - Line {finding.get('line', '?')}"
                            ):
                                # Basic info
                                st.markdown(
                                    f"**Description:** {finding.get('description', 'N/A')}"
                                )
                                st.markdown(
                                    f"**Scanner:** {finding.get('scanner', 'N/A')}"
                                )
                                st.markdown(f"**File:** `{finding.get('file', 'N/A')}`")
                                st.markdown(f"**Line:** {finding.get('line', 'N/A')}")

                                if finding.get("cwe_id"):
                                    st.markdown(f"**CWE:** {finding['cwe_id']}")

                                if finding.get("confidence"):
                                    st.markdown(
                                        f"**Confidence:** {finding['confidence']}"
                                    )

                                # Code snippet
                                if finding.get("code_snippet"):
                                    st.markdown("**Code:**")
                                    st.code(finding["code_snippet"], language=language)

                                # LLM Explanation (if available)
                                if include_explanations and finding.get("explanation"):
                                    st.markdown("---")
                                    st.markdown("**🤖 AI-Generated Explanation:**")
                                    st.info(finding["explanation"])

                                # Fix suggestion
                                if finding.get("fix_suggestion"):
                                    st.markdown("**💡 Suggested Fix:**")
                                    st.code(
                                        finding["fix_suggestion"], language=language
                                    )

                # Display scan metadata
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(
                        f"Scanners used: {', '.join(scan_result.get('scanners_used', []))}"
                    )
                with col2:
                    duration = scan_result.get("scan_duration_seconds", 0)
                    st.caption(f"Scan completed in {duration:.2f}s")

            except (httpx.HTTPError, ValueError) as e:
                st.error(f"❌ Scan failed: {e!s}")
                st.exception(e)

    elif scan_button:
        st.warning("⚠️ Please enter some code to scan.")
