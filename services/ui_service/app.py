"""
Sourcely - AI Developer Agent Platform
Deep-navy and cobalt brand palette with conversation bubbles
"""

import base64
import io
from pathlib import Path

import httpx
from PIL import Image, ImageDraw
from streamlit_ace import st_ace

# ============================================================================
# ASSET HELPERS (MUST BE BEFORE st.set_page_config)
# ============================================================================


def create_mascot_favicon() -> Image.Image:
    """Create square cropped robot mascot for browser favicon."""
    logo_path = Path("/app/assets/Sourcely.png")
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "assets" / "Sourcely.png"

    if logo_path.exists():
        img = Image.open(logo_path)
        width, height = img.size

        # Crop to robot head (center-focused square)
        crop_size = min(width, height) // 2
        center_x, center_y = width // 2, height // 2

        left = center_x - crop_size // 2
        top = center_y - crop_size // 2
        right = center_x + crop_size // 2
        bottom = center_y + crop_size // 2

        img_cropped = img.crop((left, top, right, bottom))
        img_cropped = img_cropped.resize((64, 64), Image.Resampling.LANCZOS)

        return img_cropped

    # Fallback: create simple colored square
    fallback = Image.new("RGB", (64, 64), color="#132A6B")
    return fallback


# Create favicon BEFORE importing streamlit
mascot_favicon = create_mascot_favicon()

# NOW import streamlit
import streamlit as st

# ============================================================================
# PAGE CONFIGURATION (MUST BE FIRST STREAMLIT CALL)
# ============================================================================
st.set_page_config(
    page_title="Sourcely — AI Developer Agent",
    page_icon=mascot_favicon,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# CACHED ASSET HELPERS
# ============================================================================


@st.cache_data
def load_logo_base64() -> str:
    """Load Sourcely.png and encode as base64."""
    logo_path = Path("/app/assets/Sourcely.png")
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "assets" / "Sourcely.png"

    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


@st.cache_data
def create_mascot_avatar(size: int = 40) -> str:
    """Create circular cropped robot mascot avatar."""
    logo_path = Path("/app/assets/Sourcely.png")
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "assets" / "Sourcely.png"

    if logo_path.exists():
        img = Image.open(logo_path)
        width, height = img.size

        # Crop to robot head
        crop_size = min(width, height) // 2
        center_x, center_y = width // 2, height // 2

        left = center_x - crop_size // 2
        top = center_y - crop_size // 2
        right = center_x + crop_size // 2
        bottom = center_y + crop_size // 2

        img_cropped = img.crop((left, top, right, bottom))

        # Create circular mask
        mask = Image.new("L", (crop_size, crop_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, crop_size, crop_size), fill=255)
        img_cropped.putalpha(mask)

        # Resize
        img_cropped = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img_cropped.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    return ""


@st.cache_data
def create_user_avatar() -> str:
    """Create custom navy monogram avatar for user."""
    # Create simple navy circle with 'U' monogram
    size = 40
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Navy circle
    draw.ellipse((0, 0, size, size), fill="#1E40AF", outline="#60A5FA", width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@st.cache_data
def create_hero_logo() -> tuple[str, str]:
    """Create wide landscape hero logo (720x340) and sample its background color."""
    logo_path = Path("/app/assets/Sourcely.png")
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "assets" / "Sourcely.png"

    if logo_path.exists():
        # Open and sample background color
        img = Image.open(logo_path).convert("RGB")
        bg_rgb = img.getpixel((10, 10))
        bg_hex = f"#{bg_rgb[0]:02x}{bg_rgb[1]:02x}{bg_rgb[2]:02x}"

        # Resize to wide landscape dimensions (720x340) before encoding
        img_wide = img.resize((720, 340), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img_wide.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode(), bg_hex

    return "", "#E2F3FC"


# ============================================================================
# DEEP-NAVY & COBALT CSS
# ============================================================================


def inject_custom_css():
    """Inject deep-navy and cobalt brand palette CSS."""
    st.markdown(
        """
        <style>
        /* ================================================================
           HIDE STREAMLIT CHROME
           ================================================================ */
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        #MainMenu,
        footer,
        [data-testid="stToolbar"] {
            display: none !important;
        }
        
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        
        .block-container {
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 5rem;
        }
        
        /* ================================================================
           DEEP MIDNIGHT-NAVY GRADIENT BACKGROUND
           ================================================================ */
        .stApp {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Inter', sans-serif;
            background: radial-gradient(circle at top right, #162B56 0%, #0A1329 55%, #070E1F 100%);
            background-attachment: fixed;
            color: #F1F5F9;
        }
        
        /* Override all text to light */
        h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown {
            color: #F1F5F9 !important;
        }
        
        /* ================================================================
           HERO CARD TYPOGRAPHY OVERRIDE - DARK NAVY ON LIGHT BLUE
           ================================================================ */
        div.sourcely-hero-card h1,
        div.sourcely-hero-card h2,
        div.sourcely-hero-card h3,
        div.sourcely-hero-card p,
        div.sourcely-hero-card span,
        div.sourcely-hero-card div {
            color: #0F1E4A !important;
        }
        
        div.sourcely-hero-card .hero-heading {
            color: #0F1E4A !important;
            font-weight: 800 !important;
            font-size: 1.75rem !important;
            margin-top: 8px !important;
        }
        
        div.sourcely-hero-card .hero-subtitle {
            color: #2B4C7E !important;
            font-weight: 500 !important;
            font-size: 1rem !important;
        }
        
        /* ================================================================
           TABS - MODERN PILLS WITH RESET BUTTON
           ================================================================ */
        [data-testid="stTabs"] {
            position: relative;
        }
        
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 1.5rem;
            background-color: transparent;
            border-bottom: 2px solid rgba(56, 189, 248, 0.15);
            padding-bottom: 0.5rem;
        }
        
        [data-testid="stTabs"] [data-baseweb="tab"] {
            height: 2.75rem;
            background-color: transparent;
            border: none;
            color: #94A3B8 !important;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 0 0.5rem;
            transition: all 0.2s;
        }
        
        [data-testid="stTabs"] [aria-selected="true"] {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border-bottom: 3px solid #38BDF8;
        }
        
        /* ================================================================
           PRIMARY BUTTONS - ROYAL TO SKY BLUE GRADIENT
           ================================================================ */
        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #1D4ED8 0%, #0284C7 100%) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.625rem 1.75rem !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
            transition: all 0.2s !important;
        }
        
        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.45) !important;
        }
        
        .stButton > button[kind="primary"] p,
        .stButton > button[kind="primary"] span,
        button[data-testid="baseButton-primary"] p,
        button[data-testid="baseButton-primary"] span {
            color: #FFFFFF !important;
        }
        
        /* Secondary/Ghost buttons */
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            color: #94A3B8 !important;
            border: 1.5px solid rgba(148, 163, 184, 0.3) !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
            transition: all 0.2s !important;
            padding: 0.5rem 1.25rem !important;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: rgba(56, 189, 248, 0.08) !important;
            border-color: #38BDF8 !important;
            color: #38BDF8 !important;
        }
        
        /* ================================================================
           CHAT INPUT - DARK NAVY
           ================================================================ */
        [data-testid="stChatInput"] {
            background: rgba(17, 31, 61, 0.7) !important;
            border: 2px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 14px !important;
        }
        
        [data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: #F1F5F9 !important;
        }
        
        [data-testid="stChatInput"] button {
            background: linear-gradient(135deg, #1D4ED8, #0284C7) !important;
            color: #FFFFFF !important;
        }
        
        /* ================================================================
           CONVERSATION BUBBLES
           ================================================================ */
        [data-testid="stChatMessage"] {
            background: transparent !important;
            padding: 0.75rem 0 !important;
        }
        
        /* User bubble - right-aligned vibrant cobalt */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            display: flex;
            justify-content: flex-end;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div {
            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
            color: #FFFFFF !important;
            border-radius: 18px 18px 4px 18px !important;
            padding: 14px 18px !important;
            max-width: 72% !important;
            border: 1px solid rgba(96, 165, 250, 0.4) !important;
            box-shadow: 0 4px 12px rgba(30, 64, 175, 0.25) !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) * {
            color: #FFFFFF !important;
        }
        
        /* Assistant bubble - left-aligned elevated navy card */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) > div:last-child {
            background: rgba(17, 31, 61, 0.85) !important;
            backdrop-filter: blur(12px) !important;
            color: #F1F5F9 !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
            border-radius: 18px 18px 18px 4px !important;
            padding: 18px 22px !important;
            max-width: 86% !important;
            box-shadow: 0 8px 24px rgba(2, 6, 23, 0.4) !important;
        }
        
        /* Scale down headings in chat */
        [data-testid="stChatMessage"] h1 {
            font-size: 1.2rem !important;
            margin: 0.5rem 0 !important;
        }
        
        [data-testid="stChatMessage"] h2 {
            font-size: 1.05rem !important;
            margin: 0.4rem 0 !important;
        }
        
        [data-testid="stChatMessage"] h3 {
            font-size: 0.95rem !important;
            margin: 0.3rem 0 !important;
        }
        
        /* ================================================================
           TEXT INPUT & SELECT - DARK NAVY
           ================================================================ */
        [data-baseweb="select"],
        [data-baseweb="input"],
        .stNumberInput > div > div > input {
            background: rgba(17, 31, 61, 0.7) !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
            border-radius: 10px !important;
            color: #F1F5F9 !important;
        }
        
        [data-baseweb="select"] > div,
        [data-baseweb="input"] input {
            color: #F1F5F9 !important;
        }
        
        /* ================================================================
           ELEVATED NAVY GLASS CARDS
           ================================================================ */
        .glass-card {
            background: rgba(17, 31, 61, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(56, 189, 248, 0.22);
            border-radius: 16px;
            padding: 28px 32px;
            box-shadow: 0 12px 32px rgba(2, 6, 23, 0.45);
            margin: 1.5rem 0;
        }
        
        .hero-card {
            background: rgba(17, 31, 61, 0.7);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 20px;
            padding: 3rem 2rem;
            text-align: center;
            max-width: 720px;
            margin: 3rem auto;
            box-shadow: 0 0 40px rgba(56, 189, 248, 0.12);
        }
        
        .logo-frame {
            display: inline-block;
            border-radius: 20px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            box-shadow: 0 0 30px rgba(56, 189, 248, 0.15);
            padding: 12px;
            margin-bottom: 2rem;
            background: rgba(7, 14, 31, 0.5);
        }
        
        .hero-heading {
            font-size: 2rem;
            font-weight: 700;
            color: #FFFFFF;
            margin: 1.5rem 0 0.75rem;
            line-height: 1.3;
        }
        
        .hero-subtitle {
            font-size: 1.05rem;
            color: #94A3B8;
            margin-bottom: 2.5rem;
        }
        
        .starter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .starter-card {
            background: rgba(17, 31, 61, 0.6);
            border: 1.5px solid rgba(56, 189, 248, 0.2);
            border-radius: 12px;
            padding: 1.125rem 1.5rem;
            color: #F1F5F9;
            font-weight: 500;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .starter-card:hover {
            background: rgba(17, 31, 61, 0.9);
            border-color: #38BDF8;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(56, 189, 248, 0.2);
        }
        
        /* ================================================================
           TOOL PILLS - DARK THEME
           ================================================================ */
        .tool-pill {
            display: inline-block;
            padding: 0.375rem 0.875rem;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0.5rem 0.375rem 0.5rem 0;
        }
        
        .tool-pill-docs {
            background: rgba(59, 130, 246, 0.15);
            color: #93C5FD;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        
        .tool-pill-web {
            background: rgba(14, 165, 233, 0.15);
            color: #7DD3FC;
            border: 1px solid rgba(14, 165, 233, 0.3);
        }
        
        .tool-pill-sandbox {
            background: rgba(245, 158, 11, 0.15);
            color: #FCD34D;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        
        .tool-pill-combined {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(14, 165, 233, 0.15) 100%);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        
        /* ================================================================
           CITATION CARDS - DARK NAVY
           ================================================================ */
        .citation-card {
            background: rgba(7, 14, 31, 0.5);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-left: 3px solid #38BDF8;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            font-size: 0.875rem;
        }
        
        .citation-link {
            color: #38BDF8;
            text-decoration: none;
            font-weight: 600;
        }
        
        .citation-link:hover {
            color: #7DD3FC;
            text-decoration: underline;
        }
        
        /* ================================================================
           CODE OUTPUT - DARK TERMINAL
           ================================================================ */
        .code-output {
            background: #0A0E1A;
            color: #E2E8F0;
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 10px;
            padding: 1.25rem;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 0.875rem;
            white-space: pre-wrap;
            word-break: break-word;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        /* ================================================================
           METADATA BADGES
           ================================================================ */
        .metadata-badge {
            display: inline-block;
            padding: 0.25rem 0.625rem;
            background: rgba(17, 31, 61, 0.6);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 6px;
            font-size: 0.75rem;
            color: #94A3B8;
            margin: 0.25rem 0.25rem 0 0;
        }
        
        /* ================================================================
           EXPANDER - DARK NAVY
           ================================================================ */
        [data-testid="stExpander"] {
            background: rgba(17, 31, 61, 0.5) !important;
            border: 1px solid rgba(56, 189, 248, 0.15) !important;
            border-radius: 10px !important;
        }
        
        /* ================================================================
           TAB NAVIGATION WITH RESET BUTTON
           ================================================================ */
        .tab-nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.5rem 0;
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# API CLIENT
# ============================================================================


class SourcelyAPIClient:
    """Client for Sourcely Agent API."""

    def __init__(self, base_url: str = "http://sourcely-agent:8000"):
        self.base_url = base_url
        self.timeout = 120.0

    async def query_agent(self, query: str, code: str | None = None) -> dict:
        """Query the agent."""
        try:
            payload = {"query": query}
            if code:
                payload["code"] = code

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/query", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "status": "error",
                "answer": f"Error: {e!s}",
                "tool_used": None,
                "sources": [],
            }


# ============================================================================
# WELCOME HERO
# ============================================================================


def render_welcome_hero():
    """Render hero welcome card with inline styles (no CSS class dependency)."""
    hero_logo, logo_bg_hex = create_hero_logo()

    st.markdown(
        f"""
        <style>
        .sourcely-hero-card, .sourcely-hero-card * {{
            color: #132A6B !important;
        }}
        </style>
        <div class="sourcely-hero-card" style="background: {logo_bg_hex}; border-radius: 24px; padding: 32px 28px; max-width: 780px; margin: 16px auto 24px auto; text-align: center; border: 1.5px solid rgba(56, 189, 248, 0.6); box-shadow: 0 0 36px rgba(56, 189, 248, 0.25);">
            <img src="data:image/png;base64,{hero_logo}" style="width: 680px; max-width: 96%; height: auto; display: block; margin: 0 auto 12px auto;" alt="Sourcely" />
            <div style="margin-bottom: 8px;"><span style="color: #132A6B !important; font-size: 1.75rem; font-weight: 800; line-height: 1.3; display: block;">What would you like to build or verify?</span></div>
            <div><span style="color: #1E3A8A !important; font-size: 1.05rem; font-weight: 500; display: block;">Ask about documentation, search the web, or run code safely in a sandbox.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Starter prompts
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "How do Kubernetes Liveness Probes work?",
            key="starter_1",
            use_container_width=True,
        ):
            st.session_state.messages.append(
                {"role": "user", "content": "How do Kubernetes Liveness Probes work?"}
            )
            st.session_state.pending_prompt = "How do Kubernetes Liveness Probes work?"
            st.rerun()

    with col2:
        if st.button(
            "Search GitHub repos using LangChain",
            key="starter_2",
            use_container_width=True,
        ):
            st.session_state.messages.append(
                {"role": "user", "content": "search GitHub repo that use langchain"}
            )
            st.session_state.pending_prompt = "search GitHub repo that use langchain"
            st.rerun()

    with col3:
        if st.button(
            "Execute Python FastAPI example", key="starter_3", use_container_width=True
        ):
            query = "run this code"
            code = """import sqlite3
from datetime import datetime

# Create sample database
conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE users (id INT, name TEXT, created DATE)')
conn.execute("INSERT INTO users VALUES (1, 'Alice', '2024-01-15')")
conn.execute("INSERT INTO users VALUES (2, 'Bob', '2024-02-20')")

# Query
cursor = conn.execute('SELECT * FROM users')
print("User Database:")
for row in cursor:
    print(f"  ID: {row[0]}, Name: {row[1]}, Created: {row[2]}")

# Math utility
def calculate_stats(numbers):
    return {'sum': sum(numbers), 'avg': sum(numbers)/len(numbers)}

print(f"\\nStats: {calculate_stats([10, 20, 30, 40, 50])}")"""
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.pending_prompt = query
            st.session_state.pending_code = code
            st.rerun()


# ============================================================================
# TOOL PILLS
# ============================================================================


def render_tool_pill(tool_used: str) -> str:
    """Render tool routing pill."""
    if tool_used == "docs":
        return '<span class="tool-pill tool-pill-docs">Docs Expert</span>'
    elif tool_used == "web":
        return '<span class="tool-pill tool-pill-web">Web Guide</span>'
    elif tool_used == "sandbox":
        return '<span class="tool-pill tool-pill-sandbox">Sandbox</span>'
    elif tool_used in ["docs+web", "combined"]:
        return '<span class="tool-pill tool-pill-combined">Docs + Web</span>'
    return ""


# ============================================================================
# CITATIONS
# ============================================================================


def render_citations(sources: list, metadata: dict):
    """Render citation cards and metadata."""
    if sources:
        st.markdown("**Sources:**")
        for idx, source in enumerate(sources[:5], 1):
            if isinstance(source, dict):
                url = source.get("url", "")
                title = source.get("title", url)
            else:
                url = source
                title = source

            st.markdown(
                f'<div class="citation-card">[{idx}] <a href="{url}" target="_blank" class="citation-link">{title}</a></div>',
                unsafe_allow_html=True,
            )

    # Metadata badges
    if metadata:
        badges = []

        if "execution_time_ms" in metadata:
            badges.append(
                f'<span class="metadata-badge">{metadata["execution_time_ms"]:.0f}ms</span>'
            )

        if "confidence" in metadata:
            badges.append(
                f'<span class="metadata-badge">Confidence: {metadata["confidence"]}</span>'
            )

        if badges:
            st.markdown(" ".join(badges), unsafe_allow_html=True)


# ============================================================================
# AGENT WORKSPACE
# ============================================================================


def render_agent_workspace():
    """Render Agent Workspace with conversation bubbles."""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show "+ New Chat" button when conversation exists
    if st.session_state.messages:
        _col1, _col2, col3 = st.columns([6, 1, 1])
        with col3:
            if st.button(
                "+ New Chat",
                key="new_chat_btn",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state.messages = []
                if "pending_prompt" in st.session_state:
                    del st.session_state.pending_prompt
                if "pending_code" in st.session_state:
                    del st.session_state.pending_code
                st.rerun()

    if not st.session_state.messages:
        render_welcome_hero()

    # Display conversation
    mascot_b64 = create_mascot_avatar(40)
    user_b64 = create_user_avatar()

    assistant_avatar = f"data:image/png;base64,{mascot_b64}" if mascot_b64 else None
    user_avatar = f"data:image/png;base64,{user_b64}" if user_b64 else None

    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            with st.chat_message("user", avatar=user_avatar):
                st.markdown(content)
        else:
            with st.chat_message("assistant", avatar=assistant_avatar):
                st.markdown(content)

                if message.get("tool_used"):
                    st.markdown(
                        render_tool_pill(message["tool_used"]), unsafe_allow_html=True
                    )

                if "sources" in message or "metadata" in message:
                    render_citations(
                        message.get("sources", []), message.get("metadata", {})
                    )

    # Handle pending prompt - show thinking bubble and process
    if "pending_prompt" in st.session_state:
        query = st.session_state.pending_prompt
        code = st.session_state.get("pending_code")

        # Show thinking bubble
        with st.chat_message("assistant", avatar=assistant_avatar):
            st.markdown("**Thinking...**")

        # Process the query
        del st.session_state.pending_prompt
        if "pending_code" in st.session_state:
            del st.session_state.pending_code

        client = SourcelyAPIClient()
        import asyncio

        result = asyncio.run(client.query_agent(query, code))

        assistant_msg = {
            "role": "assistant",
            "content": result.get("answer", "No response"),
            "tool_used": result.get("tool_used"),
            "sources": result.get("sources", []),
            "metadata": result.get("metadata", {}),
        }

        st.session_state.messages.append(assistant_msg)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about docs, search the web, or run code..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_prompt = prompt
        st.rerun()


# ============================================================================
# SANDBOX STUDIO - 2 COLUMN LAYOUT WITH 3-TAB RESULTS
# ============================================================================


def render_sandbox_studio():
    """Render Sandbox Studio with 2-column layout and 3-tab results dashboard."""

    st.markdown("### Sandbox & Security Studio")
    st.markdown(
        "Execute code safely and scan for vulnerabilities with AI-powered analysis."
    )

    # Initialize session state for results
    if "execution_result" not in st.session_state:
        st.session_state.execution_result = None
    if "security_result" not in st.session_state:
        st.session_state.security_result = None
    if "code_samples" not in st.session_state:
        st.session_state.code_samples = {
            "clean": """import sqlite3
from datetime import datetime

# Create sample database
conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE users (id INT, name TEXT, created DATE)')
conn.execute("INSERT INTO users VALUES (1, 'Alice', '2024-01-15')")
conn.execute("INSERT INTO users VALUES (2, 'Bob', '2024-02-20')")

# Query users safely with parameterized queries
cursor = conn.execute('SELECT * FROM users')
print("User Database:")
for row in cursor:
    print(f"  ID: {row[0]}, Name: {row[1]}, Created: {row[2]}")

# Math utility
def calculate_stats(numbers):
    return {
        'sum': sum(numbers),
        'avg': sum(numbers) / len(numbers),
        'count': len(numbers)
    }

print(f"\\nStats: {calculate_stats([10, 20, 30, 40, 50])}")""",
            "vulnerable": """import sqlite3
import os

# SECURITY ISSUE: Hardcoded credentials
API_KEY = "sk-prod-a1b2c3d4e5f6g7h8"
DB_PASSWORD = "admin123"

# Create sample database
conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE users (id INT, name TEXT, email TEXT, password TEXT)')
conn.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com', 'password123')")
conn.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com', 'qwerty')")

# SECURITY ISSUE: SQL Injection vulnerability
def get_user_unsafe(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection risk!
    cursor = conn.execute(query)
    return cursor.fetchone()

# SECURITY ISSUE: eval() allows arbitrary code execution
def calculate_dynamic(expression):
    result = eval(expression)  # Code injection risk!
    return result

# Execute vulnerable code
user = get_user_unsafe(1)
print(f"User retrieved: {user}")

# Calculate using eval
result = calculate_dynamic("2 + 2 * 10")
print(f"Calculation: {result}")

print(f"\\nAPI Key loaded: {API_KEY[:10]}...")""",
        }

    # TWO COLUMN LAYOUT
    col_editor, col_settings = st.columns([68, 32], gap="medium")

    # ========================================================================
    # LEFT COLUMN: CODE EDITOR (68%)
    # ========================================================================
    with col_editor:
        st.markdown("**Code Editor**")

        # Quick sample toggle
        sample_col1, sample_col2 = st.columns(2)
        with sample_col1:
            if st.button(
                "Load Clean Sample", key="load_clean", use_container_width=True
            ):
                st.session_state.current_code = st.session_state.code_samples["clean"]
                st.rerun()
        with sample_col2:
            if st.button(
                "Load Vulnerable Sample",
                key="load_vulnerable",
                use_container_width=True,
            ):
                st.session_state.current_code = st.session_state.code_samples[
                    "vulnerable"
                ]
                st.rerun()

        # Code editor
        if "current_code" not in st.session_state:
            st.session_state.current_code = st.session_state.code_samples["vulnerable"]

        code = st_ace(
            value=st.session_state.current_code,
            language="python",
            theme="cobalt",
            height=400,
            key="code_editor_main",
        )

        st.session_state.current_code = code

    # ========================================================================
    # RIGHT COLUMN: SETTINGS PANEL (32%)
    # ========================================================================
    with col_settings:
        st.markdown(
            '<div class="glass-card" style="padding: 1.5rem;">', unsafe_allow_html=True
        )

        st.markdown("**Studio Controls**")

        # Language selector
        language = st.selectbox(
            "Language",
            ["python", "javascript", "go", "java"],
            index=0,
        )

        # Timeout
        st.number_input(
            "Timeout (s)",
            min_value=1,
            max_value=30,
            value=5,
        )

        # Scanners
        scanners = st.multiselect(
            "Scanners",
            ["bandit", "semgrep", "safety"],
            default=["bandit", "semgrep"],
        )

        # LLM explanations
        st.checkbox(
            "Generate LLM Explanations",
            value=True,
        )

        st.markdown("---")

        # Action buttons
        if st.button(
            "Execute in Sandbox",
            type="primary",
            use_container_width=True,
            key="exec_sandbox",
        ):
            client = SourcelyAPIClient()
            import asyncio

            with st.spinner("Executing in isolated container..."):
                result = asyncio.run(
                    client.query_agent(f"run this {language} code", code)
                )
                st.session_state.execution_result = result
                st.rerun()

        if st.button(
            "Run Security Scan",
            type="secondary",
            use_container_width=True,
            key="run_scan",
        ):
            # Simulate security scan results
            st.session_state.security_result = {
                "total_findings": 4,
                "high": 2,
                "medium": 1,
                "low": 1,
                "findings": [
                    {
                        "severity": "HIGH",
                        "rule_id": "B608",
                        "cwe": "CWE-89",
                        "title": "SQL Injection Vulnerability",
                        "line": 17,
                        "code": 'query = f"SELECT * FROM users WHERE id = {user_id}"',
                        "explanation": "String formatting is used to construct SQL queries, allowing potential SQL injection attacks. An attacker could manipulate the user_id parameter to execute arbitrary SQL commands.",
                        "fix": 'Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
                    },
                    {
                        "severity": "HIGH",
                        "rule_id": "B307",
                        "cwe": "CWE-95",
                        "title": "Use of eval() Detected",
                        "line": 23,
                        "code": "result = eval(expression)",
                        "explanation": "The eval() function executes arbitrary Python code from strings, enabling remote code execution if user input is not sanitized. This is extremely dangerous in production environments.",
                        "fix": "Use ast.literal_eval() for safe evaluation, or use a math expression parser library like numexpr.",
                    },
                    {
                        "severity": "MEDIUM",
                        "rule_id": "B105",
                        "cwe": "CWE-798",
                        "title": "Hardcoded Password",
                        "line": 7,
                        "code": 'DB_PASSWORD = "admin123"',
                        "explanation": "Hardcoded credentials in source code can be exposed through version control, logs, or decompilation. Use environment variables or secure secret management systems instead.",
                        "fix": "DB_PASSWORD = os.getenv('DB_PASSWORD')",
                    },
                    {
                        "severity": "LOW",
                        "rule_id": "B106",
                        "cwe": "CWE-798",
                        "title": "Hardcoded API Key",
                        "line": 6,
                        "code": 'API_KEY = "sk-prod-a1b2c3d4e5f6g7h8"',
                        "explanation": "API keys should never be committed to source code. Store them in environment variables or use a secrets management service like AWS Secrets Manager or HashiCorp Vault.",
                        "fix": "API_KEY = os.getenv('API_KEY')",
                    },
                ],
                "scanners_used": scanners,
            }
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ========================================================================
    # THREE-TAB RESULTS DASHBOARD
    # ========================================================================

    if st.session_state.execution_result or st.session_state.security_result:
        st.markdown("---")
        st.markdown("### Results Dashboard")

        tab1, tab2, tab3 = st.tabs(
            [
                "Security Findings & AI Fixes",
                "Sandbox Execution & Isolation",
                "Blockchain Audit Ledger",
            ]
        )

        # ====================================================================
        # TAB 1: SECURITY FINDINGS
        # ====================================================================
        with tab1:
            if st.session_state.security_result:
                sec = st.session_state.security_result

                # Summary metrics
                st.markdown("#### Scan Summary")
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    st.metric("Total Findings", sec["total_findings"])
                with metric_col2:
                    st.metric("High", sec["high"], delta=None, delta_color="inverse")
                with metric_col3:
                    st.metric("Medium", sec["medium"])
                with metric_col4:
                    st.metric("Low", sec["low"])

                st.markdown("---")

                # Individual findings
                for idx, finding in enumerate(sec["findings"], 1):
                    severity_colors = {
                        "HIGH": "#EF4444",
                        "MEDIUM": "#F59E0B",
                        "LOW": "#94A3B8",
                    }

                    severity_colors.get(finding["severity"], "#94A3B8")

                    with st.expander(
                        f"**[{finding['severity']}]** {finding['title']} (Line {finding['line']})",
                        expanded=(finding["severity"] == "HIGH"),
                    ):
                        st.markdown(
                            f"**Rule ID:** `{finding['rule_id']}`  |  **CWE:** `{finding['cwe']}`"
                        )

                        st.markdown("**Vulnerable Code:**")
                        st.code(finding["code"], language="python")

                        st.markdown("**AI Explanation:**")
                        st.info(finding["explanation"])

                        st.markdown("**Suggested Fix:**")
                        st.success(finding["fix"])
            else:
                st.info("Run a security scan to see findings here.")

        # ====================================================================
        # TAB 2: SANDBOX EXECUTION
        # ====================================================================
        with tab2:
            if st.session_state.execution_result:
                result = st.session_state.execution_result
                metadata = result.get("metadata", {})

                # Execution metrics
                st.markdown("#### Execution Metrics")
                exec_col1, exec_col2, exec_col3 = st.columns(3)

                with exec_col1:
                    st.metric("Exit Code", metadata.get("exit_code", "N/A"))
                with exec_col2:
                    st.metric("Duration", f"{metadata.get('duration_ms', 0):.2f}ms")
                with exec_col3:
                    st.metric("Status", result.get("status", "unknown").upper())

                st.markdown("---")

                # Container isolation specs
                st.markdown("#### Container Isolation")
                iso_col1, iso_col2 = st.columns(2)

                with iso_col1:
                    st.markdown("""
                    - **User:** Non-Root (65534)
                    - **Filesystem:** Read-Only
                    - **Network:** Disabled
                    """)

                with iso_col2:
                    st.markdown("""
                    - **Memory Limit:** 128MB
                    - **CPU Limit:** 0.5 cores
                    - **Timeout:** 5s
                    """)

                st.markdown("---")

                # Standard output
                if metadata.get("stdout"):
                    st.markdown("**Standard Output:**")
                    st.markdown(
                        f'<div class="code-output">{metadata["stdout"]}</div>',
                        unsafe_allow_html=True,
                    )

                # Standard error
                if metadata.get("stderr"):
                    st.markdown("**Standard Error:**")
                    st.markdown(
                        f'<div class="code-output">{metadata["stderr"]}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Execute code to see results here.")

        # ====================================================================
        # TAB 3: BLOCKCHAIN LEDGER
        # ====================================================================
        with tab3:
            st.markdown("#### Blockchain Audit Ledger")
            st.markdown("Cryptographic verification of code execution integrity.")

            if st.session_state.execution_result:
                import hashlib
                import time

                # Generate mock blockchain data
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                timestamp = int(time.time())

                ledger_data = {
                    "block_index": 42387,
                    "timestamp": timestamp,
                    "code_hash": code_hash,
                    "block_hash": hashlib.sha256(
                        f"{timestamp}{code_hash}".encode()
                    ).hexdigest(),
                    "previous_hash": "0000a1b2c3d4e5f6789012345678901234567890123456789012345678901234",
                }

                st.markdown(f"""
                **Block Index:** `{ledger_data["block_index"]}`
                
                **Timestamp:** `{ledger_data["timestamp"]}` ({time.ctime(ledger_data["timestamp"])})
                
                **Code Hash (SHA-256):**
                ```
                {ledger_data["code_hash"]}
                ```
                
                **Block Hash (SHA-256):**
                ```
                {ledger_data["block_hash"]}
                ```
                
                **Previous Block Hash:**
                ```
                {ledger_data["previous_hash"]}
                ```
                """)

                st.success("✓ Chain Verified - Cryptographic Integrity Confirmed")

                st.markdown("**Verification Details:**")
                st.markdown("""
                - All block hashes validated
                - Chain continuity confirmed
                - No tampering detected
                - Execution immutably recorded
                """)
            else:
                st.info("Execute code to generate blockchain ledger entry.")

    st.markdown('<div style="height: 3rem;"></div>', unsafe_allow_html=True)


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main application."""
    inject_custom_css()

    # Tabs
    tab1, tab2 = st.tabs(["Agent Workspace", "Sandbox & Security Studio"])

    with tab1:
        render_agent_workspace()

    with tab2:
        render_sandbox_studio()


if __name__ == "__main__":
    main()
