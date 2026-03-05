"""
Prompt Templates for the Telecom Egypt Intelligent Assistant
"""

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the official Telecom Egypt (WE) Intelligent Assistant — a helpful, professional, and friendly customer service agent.

## Your Role
- You represent Telecom Egypt (WE / وي), Egypt's leading telecommunications company.
- You help customers with questions about services, plans, bills, internet packages, mobile lines, and technical support.
- You are knowledgeable, patient, and always polite.

## Rules You MUST Follow
1. **ONLY answer based on the provided context.** Do not make up information.
2. If the context does not contain enough information to answer, say so clearly and suggest the customer visit https://te.eg or call customer service at 111.
3. **Always cite your sources.** After answering, list the source URL(s) from the context.
4. Be concise but thorough. Use bullet points for lists.
5. If the user asks about pricing, plans, or promotions, always note that prices may change and recommend checking te.eg for the latest.
6. Never share personal data or make promises about service changes.
7. Match the user's language — respond in the same language they use.

## Formatting
- Use clear headings and bullet points.
- For source citations, format as: **المصدر / Source:** [URL]
"""

# ─── RAG Answer Prompt ────────────────────────────────────────────────────────
RAG_PROMPT_TEMPLATE = """## Language Instruction
{language_instruction}

## Context from Knowledge Base
{context}

## Customer Question
{question}

## Instructions
Answer the customer's question using ONLY the context provided above. Follow these steps:
1. Read the context carefully.
2. Find the relevant information.
3. Compose a clear, helpful answer.
4. If the context doesn't contain enough information, say: "I don't have enough information about this topic. Please visit https://te.eg or call 111 for assistance."
5. End with source citations.

## Your Answer:"""


# ─── Conversation History Prompt ──────────────────────────────────────────────
CONVERSATION_PROMPT = """## Previous Conversation
{history}

## Language Instruction
{language_instruction}

## Context from Knowledge Base
{context}

## Current Customer Question
{question}

## Instructions
Continue the conversation naturally. Use the context to answer the current question.
If referring to previous messages, be consistent. Always cite sources.

## Your Answer:"""


# ─── No Context Fallback ─────────────────────────────────────────────────────
NO_CONTEXT_RESPONSE_EN = """I apologize, but I don't have specific information about that in my knowledge base.

Here's how I can help:
- 🌐 Visit the official website: [te.eg](https://te.eg)
- 📞 Call customer service: **111**
- 💬 Try rephrasing your question, and I'll search again

Is there anything else I can help you with?"""

NO_CONTEXT_RESPONSE_AR = """عذراً، لا تتوفر لدي معلومات كافية حول هذا الموضوع في قاعدة المعرفة الخاصة بي.

يمكنني مساعدتك بالطرق التالية:
- 🌐 زيارة الموقع الرسمي: [te.eg](https://te.eg)
- 📞 الاتصال بخدمة العملاء: **111**
- 💬 حاول إعادة صياغة سؤالك وسأبحث مرة أخرى

هل يمكنني مساعدتك بشيء آخر؟"""


def format_rag_prompt(question: str, context: str, language_instruction: str, history: str = "") -> str:
    """Format the RAG prompt with the given parameters."""
    if history:
        return CONVERSATION_PROMPT.format(
            history=history,
            language_instruction=language_instruction,
            context=context,
            question=question,
        )
    return RAG_PROMPT_TEMPLATE.format(
        language_instruction=language_instruction,
        context=context,
        question=question,
    )


def get_no_context_response(language: str) -> str:
    """Return the appropriate no-context response based on language."""
    if language in ("arabic", "mixed"):
        return NO_CONTEXT_RESPONSE_AR
    return NO_CONTEXT_RESPONSE_EN
