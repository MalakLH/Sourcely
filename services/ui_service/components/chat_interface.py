"""Chat interface component for interacting with the agent."""

import asyncio

import httpx
import streamlit as st
from utils.api_client import SourcelyAPIClient


def render_chat_interface(api_client: SourcelyAPIClient):
    """
    Render the chat interface for querying the agent.

    Args:
        api_client: API client for backend communication
    """
    st.header("💬 Chat with Sourcely Agent")

    st.markdown(
        """
        Ask questions about Kubernetes, Python, Docker, or request code analysis.
        The agent will route your query to the appropriate expert tool.
        """
    )

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Display metadata if available
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]

                # Show tool used
                if "tool" in metadata:
                    st.caption(f"🛠️ Tool: {metadata['tool']}")

                # Show confidence
                if "confidence" in metadata:
                    confidence = metadata["confidence"]
                    emoji = (
                        "🟢"
                        if confidence == "high"
                        else "🟡"
                        if confidence == "medium"
                        else "🔴"
                    )
                    st.caption(f"{emoji} Confidence: {confidence}")

                # Show sources
                if metadata.get("sources"):
                    with st.expander("📚 Sources"):
                        for idx, source in enumerate(metadata["sources"], 1):
                            st.markdown(f"{idx}. [{source}]({source})")

    # Chat input
    if prompt := st.chat_input("Ask me anything about docs, code, or web resources..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"), st.spinner("Thinking..."):
            try:
                response = asyncio.run(api_client.query_agent(prompt))

                # Extract answer and metadata
                answer = response.get("answer", "I couldn't generate an answer.")
                tool_result = response.get("tool_result", {})

                # Display answer
                st.markdown(answer)

                # Prepare metadata
                metadata = {}
                if tool_result:
                    metadata["tool"] = tool_result.get("tool", "unknown")
                    if "confidence" in tool_result:
                        metadata["confidence"] = tool_result["confidence"]
                    if "sources" in tool_result:
                        metadata["sources"] = tool_result["sources"]

                    # Show tool used
                    if "tool" in metadata:
                        st.caption(f"🛠️ Tool: {metadata['tool']}")

                    # Show confidence
                    if "confidence" in metadata:
                        confidence = metadata["confidence"]
                        emoji = (
                            "🟢"
                            if confidence == "high"
                            else "🟡"
                            if confidence == "medium"
                            else "🔴"
                        )
                        st.caption(f"{emoji} Confidence: {confidence}")

                    # Show sources
                    if metadata.get("sources"):
                        with st.expander("📚 Sources"):
                            for idx, source in enumerate(metadata["sources"], 1):
                                st.markdown(f"{idx}. [{source}]({source})")

                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "metadata": metadata}
                )

            except (httpx.HTTPError, ValueError) as e:
                error_msg = f"Error: {e!s}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
