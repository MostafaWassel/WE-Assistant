"""
Chat Interface UI Component
Main chat area with message history and RAG pipeline.
"""
import logging
from pathlib import Path

import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import ASSISTANT_AVATAR, USER_AVATAR
from src.llm.engine import get_llm_engine
from src.llm.prompts import SYSTEM_PROMPT, format_rag_prompt, get_no_context_response
from src.retrieval.retriever import get_retriever
from src.language.detector import detect_language, get_language_instruction

logger = logging.getLogger(__name__)


def init_session_state():
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_uploads" not in st.session_state:
        st.session_state.search_uploads = True


def render_chat():
    """Render the chat interface."""
    init_session_state()

    # Welcome message
    if not st.session_state.messages:
        _render_welcome()

    # Display chat history
    for msg in st.session_state.messages:
        avatar = ASSISTANT_AVATAR if msg["role"] == "assistant" else USER_AVATAR
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("sources"):
                _render_sources(msg["sources"])

    # Chat input
    if prompt := st.chat_input("اكتب سؤالك هنا... / Type your question here..."):
        _handle_user_input(prompt)


def _render_welcome():
    """Show a welcome message."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>🇪🇬 Welcome to Telecom Egypt Assistant</h2>
        <h3>مرحباً بك في مساعد تليكوم ايجيبت الذكي</h3>
        <p style="color: #666; font-size: 1.1rem;">
            Ask me anything about WE services, plans, bills, and more!<br>
            اسألني عن خدمات وي، الباقات، الفواتير، وأكتر!
        </p>
        <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 1rem;">
            <code>What internet plans are available?</code>
            <code>ازاي أشحن الخط بتاعي؟</code>
            <code>ما هي باقات الإنترنت؟</code>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _handle_user_input(user_query: str):
    """Process user input through the RAG pipeline."""

    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_query)

    # Generate response
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("🔍 Searching knowledge base..."):
            response, sources = _rag_pipeline(user_query)

        st.markdown(response)
        if sources:
            _render_sources(sources)

    # Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "sources": sources,
    })


def _rag_pipeline(query: str) -> tuple[str, list[str]]:
    """
    Full RAG pipeline:
    1. Detect language
    2. Retrieve relevant context
    3. Format prompt
    4. Generate response
    """
    # 1. Language detection
    lang_info = detect_language(query)
    lang_instruction = get_language_instruction(query)
    logger.info(f"Language detected: {lang_info}")

    # 2. Retrieve context
    retriever = get_retriever()
    include_uploads = st.session_state.get("search_uploads", True)
    results = retriever.search(query, include_uploads=include_uploads)

    # 3. Format context
    if not results:
        no_context = get_no_context_response(lang_info["language"])
        return no_context, []

    context, sources = retriever.format_context(results)

    # 4. Build conversation history (last 3 exchanges)
    history = _format_history(st.session_state.messages[-6:])  # last 3 pairs

    # 5. Format prompt
    user_prompt = format_rag_prompt(
        question=query,
        context=context,
        language_instruction=lang_instruction,
        history=history,
    )

    # 6. Generate response
    engine = get_llm_engine()
    response = engine.generate(SYSTEM_PROMPT, user_prompt)

    return response, sources


def _format_history(messages: list[dict]) -> str:
    """Format recent chat history for context."""
    if not messages:
        return ""
    parts = []
    for msg in messages:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        parts.append(f"{role}: {msg['content'][:300]}")
    return "\n".join(parts)


def _render_sources(sources: list[str]):
    """Render source citations."""
    if not sources:
        return

    with st.expander("📌 Sources / المصادر", expanded=False):
        for src in sources:
            if src.startswith("http"):
                st.markdown(f"- 🌐 [{src}]({src})")
            else:
                st.markdown(f"- 📄 {src}")
