"""
🇪🇬 Telecom Egypt Intelligent Assistant
Main Streamlit Application — Inspired by streamlit/demo-ai-assistant
"""
import sys
import datetime
import time
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from htbuilder import div, styles
from htbuilder.units import rem

from config.settings import (
    WEBSITE_COLLECTION, UPLOADS_COLLECTION,
)
from src.llm.engine import get_llm_engine
from src.llm.prompts import SYSTEM_PROMPT, format_rag_prompt, get_no_context_response
from src.retrieval.retriever import get_retriever
from src.language.detector import detect_language, get_language_instruction
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.indexer import build_uploads_vectorstore, load_existing_vectorstore

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WE Intelligent Assistant",
    page_icon="🇪🇬",
    layout="centered",
)

# ─── Constants ────────────────────────────────────────────────────────────────

HISTORY_LENGTH = 6
MIN_TIME_BETWEEN_REQUESTS = datetime.timedelta(seconds=1)

SUGGESTIONS = {
    "ما هي باقات الإنترنت المنزلي؟": (
        "ما هي باقات الإنترنت المنزلي المتاحة من WE وأسعارها؟"
    ),
    "What mobile plans are available?": (
        "What mobile plans does WE offer? Tell me about prepaid and postpaid options."
    ),
    "ازاي ادفع الفاتورة؟": (
        "ازاي اقدر ادفع فاتورة التليفون الأرضي أو النت؟"
    ),
    "Tell me about 5G services": (
        "What 5G services and devices does Telecom Egypt WE offer?"
    ),
    "عايز أعرف عن باقات الموبايل": (
        "عايز اعرف الباقات المتاحة للموبايل من وي، سواء فاتورة أو كارت"
    ),
}

SUPPORTED_UPLOAD_TYPES = ["pdf", "docx", "txt", "html", "png", "jpg", "jpeg"]


# ─── Helper Functions ─────────────────────────────────────────────────────────


def history_to_text(chat_history: list[dict]) -> str:
    """Converts chat history into a string."""
    return "\n".join(f"[{h['role']}]: {h['content'][:300]}" for h in chat_history)


def rag_pipeline(user_query: str) -> tuple[str, list[str]]:
    """
    Full RAG pipeline:
    1. Detect language  →  2. Retrieve context  →  3. Format prompt  →  4. Generate
    """
    # 1 — Language detection
    lang_info = detect_language(user_query)
    lang_instruction = get_language_instruction(user_query)
    logger.info(f"Language: {lang_info}")

    # 2 — Retrieve context
    retriever = get_retriever()
    include_uploads = st.session_state.get("search_uploads", True)
    results = retriever.search(user_query, include_uploads=include_uploads)

    # 3 — No context fallback
    if not results:
        return get_no_context_response(lang_info["language"]), []

    context, sources = retriever.format_context(results)

    # 4 — Build conversation history
    recent = st.session_state.messages[-HISTORY_LENGTH:] if st.session_state.get("messages") else []
    history = history_to_text(recent) if recent else ""

    # 5 — Format prompt
    user_prompt = format_rag_prompt(
        question=user_query,
        context=context,
        language_instruction=lang_instruction,
        history=history,
    )

    # 6 — Generate
    engine = get_llm_engine()
    response = engine.generate(SYSTEM_PROMPT, user_prompt)
    return response, sources


@st.cache_data(ttl=30)
def check_system_status() -> dict:
    """Check all system components — cached 30s."""
    status = {"ollama": False, "knowledge_base": False, "kb_chunks": 0}
    engine = get_llm_engine()
    status["ollama"] = engine.is_available()
    ws = load_existing_vectorstore(WEBSITE_COLLECTION)
    if ws:
        status["knowledge_base"] = True
        status["kb_chunks"] = ws._collection.count()
    return status


def process_uploaded_files(uploaded_files) -> int:
    """Process uploaded files and index into ChromaDB. Returns doc count."""
    from config.settings import UPLOAD_DIR
    loader = DocumentLoader()
    all_docs = []
    for uf in uploaded_files:
        path = UPLOAD_DIR / uf.name
        path.write_bytes(uf.getbuffer())
        all_docs.extend(loader.load(path))
    if all_docs:
        build_uploads_vectorstore(all_docs)
        get_retriever().reload_uploads()
        return len(all_docs)
    return 0


def render_sources(sources: list[str]):
    """Render source citations."""
    if not sources:
        return
    with st.expander("Sources / المصادر", expanded=False):
        for src in sources:
            if src.startswith("http"):
                st.markdown(f"- [{src}]({src})")
            else:
                st.markdown(f"- {src}")


def show_feedback_controls(message_index: int):
    """Feedback popover for each assistant message."""
    st.write("")
    with st.popover("How did I do? / كيف كان ردي؟"):
        with st.form(key=f"feedback-{message_index}", border=False):
            with st.container():
                st.markdown(":small[Rating / التقييم]")
                st.feedback(options="stars")
            st.text_area("Details (optional)")
            ""  # spacer
            if st.form_submit_button("Send / إرسال"):
                st.toast("Thank you! شكراً 🙏")


@st.dialog("About / عن المساعد")
def show_about_dialog():
    st.markdown("""
    **Telecom Egypt (WE) Intelligent Assistant**

    | Component | Detail |
    |-----------|--------|
    | LLM | qwen3:1.7b via Ollama |
    | Embeddings | nomic-embed-text |
    | Vector Store | ChromaDB |
    | Knowledge | [te.eg](https://te.eg) |
    | Languages | Arabic · Egyptian · English |
    | Uploads | PDF · DOCX · TXT · HTML · Images |

    ---
    All data stays local — nothing leaves your machine.
    """)


@st.dialog("Upload Documents / رفع ملفات")
def show_upload_dialog():
    st.markdown("Upload documents to extend the knowledge base.")
    st.caption("Supported: PDF, DOCX, TXT, HTML, PNG, JPG")
    uploaded_files = st.file_uploader(
        "Choose files / اختر ملفات",
        type=SUPPORTED_UPLOAD_TYPES,
        accept_multiple_files=True,
        key="dialog_uploader",
    )
    if uploaded_files:
        if st.button("Process & Index", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                count = process_uploaded_files(uploaded_files)
            if count > 0:
                st.success(f"Indexed {count} document(s)!")
                st.session_state["uploaded_count"] = st.session_state.get("uploaded_count", 0) + count
            else:
                st.warning("No text could be extracted.")


# ─────────────────────────────────────────────────────────────────────────────
# DRAW THE UI
# ─────────────────────────────────────────────────────────────────────────────

# Title row
title_row = st.container(horizontal=True, vertical_alignment="bottom")

with title_row:
    st.title("WE Intelligent Assistant", anchor=False, width="stretch")

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### System Status")
    status = check_system_status()

    if status["ollama"]:
        st.markdown("**Ollama:** Connected")
    else:
        st.markdown("**Ollama:** Not reachable")
        st.warning("Start Ollama: `ollama serve`")

    if status["knowledge_base"]:
        st.markdown(f"**Knowledge Base:** {status['kb_chunks']} chunks")
    else:
        st.markdown("**Knowledge Base:** Not built yet")

    up_count = st.session_state.get("uploaded_count", 0)
    if up_count > 0:
        st.markdown(f"**User Docs:** {up_count} indexed")

    st.divider()
    st.markdown("### Settings")
    st.toggle("Include uploaded docs in search", value=True, key="search_uploads")

    st.divider()
    st.markdown("""
    [te.eg](https://te.eg) · 111 · Fully local
    """)

# ─── Chat State Logic ────────────────────────────────────────────────────────

user_just_asked_initial = (
    "initial_question" in st.session_state and st.session_state.initial_question
)
user_just_clicked_suggestion = (
    "selected_suggestion" in st.session_state and st.session_state.selected_suggestion
)
user_first_interaction = user_just_asked_initial or user_just_clicked_suggestion
has_history = "messages" in st.session_state and len(st.session_state.messages) > 0

# ─── Landing screen ──────────────────────────────────────────────────────────

if not user_first_interaction and not has_history:
    st.session_state.messages = []

    st.markdown(
        "<p style='text-align:center;color:#8b5cf6;font-size:1.05rem;'>"
        "مساعد تليكوم ايجيبت الذكي — Ask about WE services, plans, bills & more"
        "</p>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.chat_input(
            "اكتب سؤالك هنا... / Ask your question here...",
            key="initial_question",
        )

        st.pills(
            label="Examples",
            label_visibility="collapsed",
            options=SUGGESTIONS.keys(),
            key="selected_suggestion",
        )

    # Action buttons at the bottom
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "Upload Documents",
            use_container_width=True,
            on_click=show_upload_dialog,
        )
    with col2:
        st.button(
            "About",
            use_container_width=True,
            on_click=show_about_dialog,
        )

    st.stop()


# ─── Active chat screen ──────────────────────────────────────────────────────

# Show chat input at the bottom
user_message = st.chat_input("اكتب سؤالك... / Ask a follow-up...")

if not user_message:
    if user_just_asked_initial:
        user_message = st.session_state.initial_question
    if user_just_clicked_suggestion:
        user_message = SUGGESTIONS[st.session_state.selected_suggestion]

# Add action buttons to title row
with title_row:

    def clear_conversation():
        st.session_state.messages = []
        st.session_state.initial_question = None
        st.session_state.selected_suggestion = None

    st.button("Restart", icon=":material/refresh:", on_click=clear_conversation)
    st.button("Upload", icon=":material/upload_file:", on_click=show_upload_dialog)

# Init timestamp
if "prev_question_timestamp" not in st.session_state:
    st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.container()  # ghost message fix

        st.markdown(message["content"])

        if message["role"] == "assistant":
            if message.get("sources"):
                render_sources(message["sources"])
            show_feedback_controls(i)

# ─── Handle new user message ─────────────────────────────────────────────────

if user_message:
    # Fix LaTeX rendering
    user_message = user_message.replace("$", r"\$")

    # Display user bubble
    with st.chat_message("user"):
        st.text(user_message)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching knowledge base... / جاري البحث..."):
            # Rate limit
            now = datetime.datetime.now()
            diff = now - st.session_state.prev_question_timestamp
            st.session_state.prev_question_timestamp = now
            if diff < MIN_TIME_BETWEEN_REQUESTS:
                time.sleep(diff.seconds + diff.microseconds * 0.001)

            clean_query = user_message.replace("'", "").replace(r"\$", "$")

        with st.spinner("🤖 Thinking... / جاري التفكير..."):
            response, sources = rag_pipeline(clean_query)

        # Container fixes ghost message bug
        with st.container():
            st.markdown(response)

            # Persist to history
            st.session_state.messages.append({"role": "user", "content": user_message})
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": sources,
            })

            if sources:
                render_sources(sources)
            show_feedback_controls(len(st.session_state.messages) - 1)
