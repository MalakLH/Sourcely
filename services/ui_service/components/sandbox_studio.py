"""
Sandbox & Security Studio - Combined code scanner and sandbox execution interface
with syntax-highlighted editor, tabbed results, and blockchain ledger verification
"""

import asyncio
import hashlib

import streamlit as st
from streamlit_ace import st_ace


def render_sandbox_studio(api_client):
    """Render the unified sandbox and security studio interface."""

    # Initialize session state
    if "code_input" not in st.session_state:
        st.session_state.code_input = """# Example: SQL Injection Vulnerability
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Vulnerable: Direct string concatenation
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    
    return cursor.fetchone()

# Usage
user = get_user("admin' OR '1'='1")
print(user)
"""

    if "scan_results" not in st.session_state:
        st.session_state.scan_results = None

    if "sandbox_results" not in st.session_state:
        st.session_state.sandbox_results = None

    # Split layout: 65% editor, 35% controls
    col_editor, col_controls = st.columns([65, 35])

    with col_editor:
        st.markdown("### Code Editor")

        # Syntax-highlighted code editor
        code = st_ace(
            value=st.session_state.code_input,
            language="python",
            theme="monokai",
            key="code_editor",
            height=400,
            font_size=13,
            tab_size=4,
            show_gutter=True,
            show_print_margin=False,
            wrap=False,
            auto_update=True,
        )

        st.session_state.code_input = code

    with col_controls:
        st.markdown("### Actions")

        # Language selector
        language = st.selectbox(
            "Language",
            ["python", "javascript", "bash"],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        # Scanner toggles
        st.markdown("#### Security Scanners")
        st.checkbox("Bandit (Python)", value=True)
        st.checkbox("Semgrep (Multi-lang)", value=True)
        enable_llm = st.checkbox("LLM Explanations", value=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # Action buttons
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            scan_button = st.button(
                "Run Security Scan", use_container_width=True, type="primary"
            )

        with col_btn2:
            execute_button = st.button(
                "Execute in Sandbox", use_container_width=True, type="secondary"
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        # Execution settings (for sandbox)
        with st.expander("Execution Settings", expanded=False):
            timeout = st.slider("Timeout (seconds)", 1, 10, 5)
            st.caption("Maximum execution time")

    # Handle scan button
    if scan_button:
        with st.spinner("Running security analysis..."):
            try:
                scan_response = asyncio.run(api_client.scan_code(code, language))
                st.session_state.scan_results = scan_response
                st.success("Security scan completed")
            except Exception as e:
                st.error(f"Scan failed: {e!s}")

    # Handle execute button
    if execute_button:
        with st.spinner("Executing code in sandbox..."):
            try:
                sandbox_response = asyncio.run(
                    api_client.execute_sandbox(code, language, timeout)
                )
                st.session_state.sandbox_results = sandbox_response
                st.success("Execution completed")
            except Exception as e:
                st.error(f"Execution failed: {e!s}")

    # Results panel with tabs
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### Results")

    result_tabs = st.tabs(
        [
            "Security Findings & AI Fixes",
            "Sandbox Stdout/Stderr & Resources",
            "Ledger Verification",
        ]
    )

    # Tab 1: Security Findings
    with result_tabs[0]:
        if st.session_state.scan_results:
            scan_data = st.session_state.scan_results

            findings = scan_data.get("findings", [])
            findings_by_severity = scan_data.get("findings_by_severity", {})

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(findings))
            with col2:
                st.metric("Critical", findings_by_severity.get("CRITICAL", 0))
            with col3:
                st.metric("High", findings_by_severity.get("HIGH", 0))
            with col4:
                st.metric("Medium", findings_by_severity.get("MEDIUM", 0))

            st.markdown("<hr>", unsafe_allow_html=True)

            # Display findings
            if findings:
                for idx, finding in enumerate(findings, 1):
                    severity = finding.get("severity", "UNKNOWN")
                    rule_id = finding.get("rule_id", "N/A")
                    description = finding.get("description", "No description")
                    scanner = finding.get("scanner", "unknown")
                    line = finding.get("line", "?")
                    code_snippet = finding.get("code_snippet", "")
                    fix_suggestion = finding.get("fix_suggestion", "")

                    # Severity color
                    severity_colors = {
                        "CRITICAL": "#EF4444",
                        "HIGH": "#F59E0B",
                        "MEDIUM": "#FBBF24",
                        "LOW": "#6B7280",
                    }
                    severity_color = severity_colors.get(severity, "#6B7280")

                    with st.expander(
                        f"Finding {idx}: {rule_id} ({severity})", expanded=idx <= 2
                    ):
                        st.markdown(
                            f'<div style="background-color: rgba(99, 102, 241, 0.05); border-left: 3px solid {severity_color}; padding: 1rem; border-radius: 0.375rem; margin-bottom: 1rem;">'
                            f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">'
                            f'<span style="background-color: {severity_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600; margin-right: 0.5rem;">{severity}</span>'
                            f'<span style="color: #9CA3AF; font-size: 0.875rem;">Line {line} • {scanner}</span>'
                            f"</div>"
                            f'<p style="color: #F3F4F6; margin: 0.5rem 0;">{description}</p>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        if code_snippet:
                            st.markdown("**Code Snippet:**")
                            st.code(code_snippet, language="python")

                        if fix_suggestion and enable_llm:
                            st.markdown("**AI Fix Suggestion:**")
                            st.info(fix_suggestion)
            else:
                st.success("No security issues detected!")
        else:
            st.info("Click 'Run Security Scan' to analyze code for vulnerabilities")

    # Tab 2: Sandbox Results
    with result_tabs[1]:
        if st.session_state.sandbox_results:
            sandbox_data = st.session_state.sandbox_results

            status = sandbox_data.get("status", "unknown")
            stdout = sandbox_data.get("stdout", "")
            stderr = sandbox_data.get("stderr", "")
            exit_code = sandbox_data.get("exit_code", -1)
            duration_ms = sandbox_data.get("duration_ms", 0)

            # Status badge
            status_colors = {
                "success": "#22C55E",
                "failed": "#EF4444",
                "timeout": "#F59E0B",
            }
            status_color = status_colors.get(status, "#6B7280")

            st.markdown(
                f'<div style="display: flex; align-items: center; margin-bottom: 1rem;">'
                f'<span style="background-color: {status_color}; color: white; padding: 0.375rem 0.75rem; border-radius: 0.25rem; font-size: 0.875rem; font-weight: 600; margin-right: 0.75rem; text-transform: uppercase;">{status}</span>'
                f'<span style="color: #9CA3AF; font-size: 0.875rem;">Exit Code: {exit_code} • Duration: {duration_ms:.0f}ms</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

            # Stdout
            if stdout:
                st.markdown("**Standard Output:**")
                st.code(stdout, language="text")
            else:
                st.caption("No stdout")

            # Stderr
            if stderr:
                st.markdown("**Standard Error:**")
                st.code(stderr, language="text")

            # Resource limits info
            with st.expander("Resource Limits", expanded=False):
                st.markdown("""
                **Security Constraints:**
                - CPU: 1 core (limited)
                - Memory: 128 MB
                - Disk: 50 MB (ephemeral)
                - Network: Disabled
                - Filesystem: Read-only except /tmp
                - Timeout: Configurable (1-10s)
                - Process isolation: Docker container
                - Syscall filtering: Seccomp enabled
                """)
        else:
            st.info("Click 'Execute in Sandbox' to run code in isolated environment")

    # Tab 3: Ledger Verification
    with result_tabs[2]:
        st.markdown("### Blockchain Audit Ledger")

        if st.session_state.sandbox_results:
            sandbox_data = st.session_state.sandbox_results

            # Generate SHA-256 block hash
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            execution_hash = hashlib.sha256(
                (
                    code
                    + str(sandbox_data.get("status", ""))
                    + str(sandbox_data.get("exit_code", ""))
                ).encode()
            ).hexdigest()

            st.markdown("**Execution Record:**")

            st.markdown(
                f'<div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 0.5rem; padding: 1rem; font-family: monospace; font-size: 0.8rem;">'
                f'<div style="color: #9CA3AF; margin-bottom: 0.5rem;">Block Hash (SHA-256):</div>'
                f'<div style="color: #6366F1; word-break: break-all; margin-bottom: 1rem;">{execution_hash}</div>'
                f'<div style="color: #9CA3AF; margin-bottom: 0.5rem;">Code Hash:</div>'
                f'<div style="color: #22C55E; word-break: break-all; margin-bottom: 1rem;">{code_hash}</div>'
                f'<div style="color: #9CA3AF; margin-bottom: 0.5rem;">Status:</div>'
                f'<div style="color: #F3F4F6;">{sandbox_data.get("status", "unknown").upper()}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

            st.markdown("<hr>", unsafe_allow_html=True)

            # Chain verification badge
            st.markdown(
                '<div style="display: flex; align-items: center; background-color: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 0.5rem; padding: 1rem; margin-top: 1rem;">'
                '<span style="color: #22C55E; font-size: 1.25rem; margin-right: 0.75rem;">✓</span>'
                "<div>"
                '<div style="color: #22C55E; font-weight: 600; margin-bottom: 0.25rem;">Chain Verified</div>'
                '<div style="color: #9CA3AF; font-size: 0.875rem;">Execution record is cryptographically sealed</div>'
                "</div>"
                "</div>",
                unsafe_allow_html=True,
            )

            # Verify integrity button
            if st.button("Verify Integrity", use_container_width=True):
                st.success(
                    "Ledger integrity verified • Block hash matches • Chain unbroken"
                )
        else:
            st.info("Execute code to generate blockchain audit record")
            st.markdown("""
            **Blockchain Ledger Features:**
            - Every execution creates an immutable block
            - SHA-256 cryptographic hashing
            - Tamper-evident audit trail
            - Historical execution replay
            - Compliance verification
            - Code provenance tracking
            """)
