"""
Agent Workspace - Clean chat interface with tool badges and confidence pills
"""

import asyncio

import httpx
import streamlit as st


def render_agent_workspace(api_client):
    """Render the agent chat workspace with starter prompts and tool routing."""

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Starter prompt pills (shown when no messages)
    if len(st.session_state.messages) == 0:
        st.markdown("### Get Started")
        st.caption("Try one of these example queries:")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "How do Kubernetes Liveness Probes work?", use_container_width=True
            ):
                st.session_state.starter_query = (
                    "How do Kubernetes Liveness Probes work?"
                )
                st.rerun()

        with col2:
            if st.button(
                "Find top FastAPI repositories on GitHub", use_container_width=True
            ):
                st.session_state.starter_query = (
                    "Find top FastAPI repositories on GitHub"
                )
                st.rerun()

        with col3:
            if st.button("Search for async Python tutorials", use_container_width=True):
                st.session_state.starter_query = "Search for async Python tutorials"
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

    # Chat messages container
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Display tool badge and confidence if available
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]

                    # Tool badge
                    tool_used = metadata.get("tool_used", "unknown")
                    tool_class = (
                        "docs"
                        if tool_used == "docs"
                        else ("web" if tool_used == "web" else "sandbox")
                    )
                    tool_display = {
                        "docs": "DOCS EXPERT",
                        "web": "WEB GUIDE",
                        "sandbox": "SANDBOX",
                        "unknown": "AGENT",
                    }.get(tool_used, "AGENT")

                    # Confidence pill
                    confidence = metadata.get("confidence", "")
                    confidence_class = "low"
                    if confidence:
                        if confidence == "high" or (
                            isinstance(confidence, (int, float)) and confidence >= 0.7
                        ):
                            confidence_class = "high"
                        elif confidence == "medium" or (
                            isinstance(confidence, (int, float)) and confidence >= 0.5
                        ):
                            confidence_class = "medium"
                        else:
                            confidence_class = "low"

                    badge_html = (
                        f'<span class="tool-badge {tool_class}">{tool_display}</span>'
                    )

                    if confidence:
                        conf_display = (
                            confidence
                            if isinstance(confidence, str)
                            else f"{float(confidence):.2f}"
                        )
                        badge_html += f'<span class="confidence-pill {confidence_class}">{conf_display}</span>'

                    # Execution time
                    exec_time = metadata.get("execution_time_ms")
                    if exec_time:
                        badge_html += f'<span style="color: #6B7280; font-size: 0.75rem; margin-left: 0.5rem;">{exec_time:.0f}ms</span>'

                    st.markdown(badge_html, unsafe_allow_html=True)

                    # Citations in collapsible section
                    citations = metadata.get("citations", [])
                    sources = metadata.get("sources", [])

                    if citations or sources:
                        with st.expander("View Sources", expanded=False):
                            if citations:
                                for idx, citation in enumerate(citations, 1):
                                    st.markdown(
                                        f'<div class="citation-card">'
                                        f'<div style="font-size: 0.75rem; color: #9CA3AF; margin-bottom: 0.25rem;">[{idx}]</div>'
                                        f'<a href="{citation}" target="_blank" style="color: #6366F1; text-decoration: none; font-size: 0.875rem;">{citation}</a>'
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )

                            if sources and isinstance(sources, list):
                                for source in sources:
                                    if isinstance(source, dict):
                                        title = source.get("title", "Source")
                                        url = source.get("url", "")
                                        snippet = source.get("snippet", "")

                                        st.markdown(
                                            f'<div class="citation-card">'
                                            f'<div style="font-weight: 500; color: #F3F4F6; margin-bottom: 0.25rem;">{title}</div>'
                                            f'<div style="font-size: 0.8rem; color: #9CA3AF; margin-bottom: 0.5rem;">{snippet[:150]}...</div>'
                                            f'<a href="{url}" target="_blank" style="color: #6366F1; text-decoration: none; font-size: 0.75rem;">{url}</a>'
                                            f"</div>",
                                            unsafe_allow_html=True,
                                        )

    # Chat input
    query = st.chat_input("Ask about documentation, search the web, or execute code...")

    # Handle starter query
    if "starter_query" in st.session_state:
        query = st.session_state.starter_query
        del st.session_state.starter_query

    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        # Call agent API
        with st.chat_message("assistant"), st.spinner("Thinking..."):
            try:
                response = asyncio.run(api_client.query_agent(query))

                answer = response.get("answer", "No response received.")
                tool_used = response.get("tool_used", "unknown")
                confidence = response.get("confidence")
                citations = response.get("citations", [])
                sources = response.get("sources", [])
                execution_time_ms = response.get("execution_time_ms", 0)

                # Display answer
                st.markdown(answer)

                # Tool badge and confidence
                tool_class = (
                    "docs"
                    if tool_used == "docs"
                    else ("web" if tool_used == "web" else "sandbox")
                )
                tool_display = {
                    "docs": "DOCS EXPERT",
                    "web": "WEB GUIDE",
                    "sandbox": "SANDBOX",
                    "unknown": "AGENT",
                }.get(tool_used, "AGENT")

                confidence_class = "low"
                if confidence:
                    if confidence == "high" or (
                        isinstance(confidence, (int, float)) and confidence >= 0.7
                    ):
                        confidence_class = "high"
                    elif confidence == "medium" or (
                        isinstance(confidence, (int, float)) and confidence >= 0.5
                    ):
                        confidence_class = "medium"
                    else:
                        confidence_class = "low"

                badge_html = (
                    f'<span class="tool-badge {tool_class}">{tool_display}</span>'
                )

                if confidence:
                    conf_display = (
                        confidence
                        if isinstance(confidence, str)
                        else f"{float(confidence):.2f}"
                    )
                    badge_html += f'<span class="confidence-pill {confidence_class}">{conf_display}</span>'

                badge_html += f'<span style="color: #6B7280; font-size: 0.75rem; margin-left: 0.5rem;">{execution_time_ms:.0f}ms</span>'

                st.markdown(badge_html, unsafe_allow_html=True)

                # Citations
                if citations or sources:
                    with st.expander("View Sources", expanded=False):
                        if citations:
                            for idx, citation in enumerate(citations, 1):
                                st.markdown(
                                    f'<div class="citation-card">'
                                    f'<div style="font-size: 0.75rem; color: #9CA3AF; margin-bottom: 0.25rem;">[{idx}]</div>'
                                    f'<a href="{citation}" target="_blank" style="color: #6366F1; text-decoration: none; font-size: 0.875rem;">{citation}</a>'
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )

                        if sources and isinstance(sources, list):
                            for source in sources:
                                if isinstance(source, dict):
                                    title = source.get("title", "Source")
                                    url = source.get("url", "")
                                    snippet = source.get("snippet", "")

                                    st.markdown(
                                        f'<div class="citation-card">'
                                        f'<div style="font-weight: 500; color: #F3F4F6; margin-bottom: 0.25rem;">{title}</div>'
                                        f'<div style="font-size: 0.8rem; color: #9CA3AF; margin-bottom: 0.5rem;">{snippet[:150]}...</div>'
                                        f'<a href="{url}" target="_blank" style="color: #6366F1; text-decoration: none; font-size: 0.75rem;">{url}</a>'
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )

                # Save assistant message with metadata
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "metadata": {
                            "tool_used": tool_used,
                            "confidence": confidence,
                            "citations": citations,
                            "sources": sources,
                            "execution_time_ms": execution_time_ms,
                        },
                    }
                )

            except (httpx.HTTPError, ValueError) as e:
                error_msg = f"Failed to get response from agent: {e!s}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg, "metadata": {}}
                )

        st.rerun()
