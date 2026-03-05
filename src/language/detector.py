"""
Language & Dialect Detector
Detects Arabic (MSA), Egyptian dialect, and English from user queries.
"""
import re
import logging

logger = logging.getLogger(__name__)

# ─── Egyptian Dialect Markers ─────────────────────────────────────────────────
# Common Egyptian Arabic words/patterns that differ from MSA
EGYPTIAN_MARKERS = [
    # Pronouns & common words
    "ازاي", "ازيك", "عامل", "عاملة", "كده", "دلوقتي", "دلوقت",
    "ليه", "ايه", "إيه", "فين", "منين", "امتى", "ممكن",
    "عشان", "علشان", "بتاع", "بتاعت", "بتاعي", "بتوع",
    "مفيش", "مافيش", "فيه", "فى",
    # Verbs
    "عايز", "عايزة", "عاوز", "عاوزة", "بيشتغل", "هيشتغل",
    "مش", "مابيشتغلش", "هتعمل", "هنعمل",
    # Common phrases
    "يا ريت", "يعني", "خلاص", "بس", "طيب", "اوكي",
    "لو سمحت", "من فضلك", "الله يخليك",
    # Telecom-specific Egyptian
    "النت", "الوايفاي", "الباقة", "الخط", "الفاتورة",
    "شحن", "رصيد", "كارت", "موبايل", "اتصالات",
]

# Compile regex patterns for Egyptian detection
EGYPTIAN_PATTERNS = [re.compile(re.escape(marker)) for marker in EGYPTIAN_MARKERS]

# ─── Arabic Detection ────────────────────────────────────────────────────────
ARABIC_RANGE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


class LanguageDetector:
    """Detect the language and dialect of user input."""

    @staticmethod
    def detect(text: str) -> dict:
        """
        Detect language of the given text.

        Returns:
            dict with keys:
                - language: "arabic", "english", or "mixed"
                - dialect: "egyptian", "msa", or None
                - confidence: float 0-1
        """
        text = text.strip()
        if not text:
            return {"language": "unknown", "dialect": None, "confidence": 0.0}

        # Count Arabic vs Latin characters
        arabic_chars = len(ARABIC_RANGE.findall(text))
        latin_chars = len(re.findall(r"[a-zA-Z]", text))
        total_alpha = arabic_chars + latin_chars

        if total_alpha == 0:
            return {"language": "unknown", "dialect": None, "confidence": 0.0}

        arabic_ratio = arabic_chars / total_alpha

        # Check for Egyptian dialect markers
        egyptian_score = 0
        for pattern in EGYPTIAN_PATTERNS:
            if pattern.search(text):
                egyptian_score += 1

        is_egyptian = egyptian_score >= 1

        if arabic_ratio > 0.5:
            # Primarily Arabic
            if is_egyptian:
                return {
                    "language": "arabic",
                    "dialect": "egyptian",
                    "confidence": min(0.7 + (egyptian_score * 0.05), 0.99),
                }
            else:
                return {
                    "language": "arabic",
                    "dialect": "msa",
                    "confidence": min(0.6 + arabic_ratio * 0.3, 0.95),
                }
        elif arabic_ratio < 0.2:
            # Primarily English
            return {
                "language": "english",
                "dialect": None,
                "confidence": min(0.6 + (1 - arabic_ratio) * 0.3, 0.95),
            }
        else:
            # Mixed
            dialect = "egyptian" if is_egyptian else "msa" if arabic_ratio > 0.3 else None
            return {
                "language": "mixed",
                "dialect": dialect,
                "confidence": 0.6,
            }

    @staticmethod
    def get_response_language_instruction(lang_info: dict) -> str:
        """Generate a language instruction for the LLM based on detected language."""
        lang = lang_info.get("language", "english")
        dialect = lang_info.get("dialect")

        if lang == "arabic":
            if dialect == "egyptian":
                return (
                    "The user is writing in Egyptian Arabic dialect. "
                    "Respond in Egyptian Arabic (العامية المصرية) to be natural and relatable. "
                    "Use common Egyptian expressions where appropriate."
                )
            else:
                return (
                    "The user is writing in Arabic (Modern Standard Arabic). "
                    "Respond in clear, formal Arabic (العربية الفصحى)."
                )
        elif lang == "mixed":
            return (
                "The user is writing in a mix of Arabic and English. "
                "Respond in the same mixed style, matching the user's tone. "
                "If the Arabic seems Egyptian dialect, use Egyptian Arabic."
            )
        else:
            return "The user is writing in English. Respond in clear, professional English."


# Module-level convenience
detector = LanguageDetector()


def detect_language(text: str) -> dict:
    """Convenience function for language detection."""
    return detector.detect(text)


def get_language_instruction(text: str) -> str:
    """Convenience function to get language instruction for a query."""
    lang_info = detector.detect(text)
    return detector.get_response_language_instruction(lang_info)
