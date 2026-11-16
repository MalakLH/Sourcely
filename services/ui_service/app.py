"""
Sourcely UI - Streamlit Interface for AI Developer Agent

A user-friendly interface for:
- Chatting with the AI agent
- Scanning code for security vulnerabilities
- Viewing documentation statistics
"""

import asyncio
import os
import streamlit as st

from components.chat_interface import render_chat_interface
from components.scanner_interface import render_scanner_interface
from utils.api_client import SourcelyAPIClient

# Page configuration
st.set_page_config(
    page_title="Sourcely AI Developer Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .stApp {
        max-width: 100%;
    }
    .main > div {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_api_client():
    """Initialize and cache the API client."""
    agent_url = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
    scanner_url = os.getenv("SCANNER_SERVICE_URL", "http://localhost:8002")
    docs_url = os.getenv("DOCS_SERVICE_URL", "http://localhost:8001")

    return SourcelyAPIClient(
        agent_url=agent_url,
        scanner_url=scanner_url,
        docs_url=docs_url,
    )


def render_sidebar():
    """Render the sidebar with service status and info."""
    with st.sidebar:
        st.title("🤖 Sourcely")
        st.caption("AI Developer Agent")

        st.divider()

        # Service status
        st.subheader("🔌 Service Status")

        api_client = get_api_client()

        try:
            health = asyncio.run(api_client.health_check())

            for service, status in health.items():
                if status:
                    st.success(f"✅ {service.capitalize()} Service")
                else:
                    st.error(f"❌ {service.capitalize()} Service")
        except Exception as e:
            st.error("Failed to check service health")
            st.caption(str(e))

        st.divider()

        # Documentation stats
        st.subheader("📚 Documentation")

        try:
            stats = asyncio.run(api_client.get_docs_stats())
            vector_store = stats.get("vector_store", {})

            if vector_store.get("exists"):
                st.metric("Indexed Chunks", vector_store.get("count", 0))
                st.caption(f"Table: {vector_store.get('table_name', 'N/A')}")
            else:
                st.warning("No documentation indexed")
        except Exception as e:
            st.caption("Unable to fetch doc stats")

        st.divider()

        # Info
        st.subheader("ℹ️ About")
        st.markdown(
            """
            **Sourcely** is an AI-powered developer assistant that provides:
            
            - 💬 Intelligent documentation search
            - 🔍 Code security scanning
            - 🌐 Web resource discovery
            - 🛠️ Code execution sandbox
            
            **Version:** 0.1.0  
            **Team:** Malak & Eya
            """
        )


def main():
    """Main application entry point."""
    # Render sidebar
    render_sidebar()

    # Main content area
    st.title("🤖 Sourcely AI Developer Agent")

    # Tabs for different interfaces
    tab1, tab2 = st.tabs(["💬 Chat Assistant", "🔍 Code Scanner"])

    with tab1:
        api_client = get_api_client()
        render_chat_interface(api_client)

    with tab2:
        api_client = get_api_client()
        render_scanner_interface(api_client)


if __name__ == "__main__":
    main()
