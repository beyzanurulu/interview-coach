"""Mülakatçı çıktısının kod ile denetimi. LLM'in kaymasına karşı son savunma hattı.

Denetimi geçemeyen metin kullanıcıya gösterilmez: model bir kez daha denenir, olmazsa
güvenli bir şablona düşülür.
"""

import re
from typing import Literal

Language = Literal["tr", "en"]

# Mülakatçı cevap kalitesi hakkında yorum yapmaz; geri bildirim rapordadır.
_PRAISE = {
    "tr": re.compile(
        r"\b(harika|mükemmel|muhteşem|süper|etkileyici|tebrik)\w*|"
        r"\b(çok\s+)?güzel\s+(bir\s+)?(örnek|cevap|yanıt|açıklama|nokta)|"
        r"\bçok\s+iyi\b|\bbaşarılı\s+bir\s+(cevap|yanıt)",
        re.IGNORECASE,
    ),
    "en": re.compile(
        r"\b(great|excellent|awesome|impressive|fantastic|perfect|amazing|congratulations)\b|"
        r"\b(solid|clear|good|nice|strong)\s+(answer|example|point|explanation|foundation)\b|"
        r"\bwell\s+done\b|\bsounds\s+(great|good|solid)\b",
        re.IGNORECASE,
    ),
}
_HIRE_CLAIM = re.compile(
    r"işe\s+alındınız|you('re|\s+are)\s+hired|teklif\s+ediyoruz", re.IGNORECASE
)
# Sistemin iç terimleri kullanıcıya sızmamalı (aday "ilan özeti" diye bir şey görmedi).
_INTERNAL_TERMS = re.compile(
    r"ilan\s+özet|cv\s+özet|job\s+summary|\bjson\b|can_follow_up|answer_type|sistem\s+talimat|"
    r"mevcut\s+veri|verilen\s+bilgi|ilanda\s+(yer\s+)?(almıyor|almamakta|bulunmuyor|belirtilmemiş)|"
    r"not\s+(mentioned|specified|listed|included)\s+in\s+the\s+(job\s+)?"
    r"(ad|posting|description|summary)|provided\s+(data|information)",
    re.IGNORECASE,
)
_CV_MENTION = re.compile(r"\bcv\b|cv'|özgeçmiş|resume|résumé", re.IGNORECASE)
_TR_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_EN_WORDS = re.compile(r"\b(the|you|your|what|how|and|have|would|could|with)\b", re.IGNORECASE)
_TR_WORDS = re.compile(
    r"\b(ve|bir|bu|için|nasıl|mısınız|misiniz|neler|hangi|sizin)\b", re.IGNORECASE
)

MAX_QUESTION_CHARS = 320
MAX_TRANSITION_CHARS = 70
MAX_ANSWER_CHARS = 450


def wrong_language(text: str, language: Language) -> bool:
    if language == "en":
        return len(_TR_CHARS.findall(text)) >= 2 or len(_TR_WORDS.findall(text)) >= 2
    return not _TR_CHARS.search(text) and len(_EN_WORDS.findall(text)) >= 2


def _common_issues(text: str, language: Language) -> list[str]:
    issues = []
    if _PRAISE[language].search(text):
        issues.append("övgü/değerlendirme içeriyor")
    if _HIRE_CLAIM.search(text):
        issues.append("işe alım/teklif ifadesi içeriyor")
    if wrong_language(text, language):
        issues.append("yanlış dilde")
    if "<veri" in text or "</veri" in text or _INTERNAL_TERMS.search(text):
        issues.append("sistem iç terimi içeriyor")
    return issues


def mentions_cv(text: str) -> bool:
    return bool(_CV_MENTION.search(text))


def utterance_issues(text: str, language: Language) -> list[str]:
    """Kullanıcıya gösterilen her mülakatçı metni için ortak kurallar."""
    return _common_issues(text, language)


def question_issues(text: str, language: Language) -> list[str]:
    """Mülakatçının soracağı bir soru (plan, takip veya açıklama) için sorunlar."""
    if not text.strip():
        return ["boş"]
    issues = _common_issues(text, language)
    if len(text) > MAX_QUESTION_CHARS:
        issues.append(f"çok uzun (>{MAX_QUESTION_CHARS} karakter)")
    if text.count("?") > 1:
        issues.append("birden fazla soru içeriyor")
    return issues


def transition_issues(text: str, language: Language) -> list[str]:
    if not text.strip():
        return []
    issues = _common_issues(text, language)
    if len(text) > MAX_TRANSITION_CHARS:
        issues.append(f"çok uzun (>{MAX_TRANSITION_CHARS} karakter)")
    if "?" in text:
        issues.append("soru içeriyor")
    return issues


def candidate_answer_issues(text: str, language: Language) -> list[str]:
    """Adayın şirkete sorduğu soruya verilen cevap için sorunlar."""
    if not text.strip():
        return ["boş"]
    issues = _common_issues(text, language)
    if len(text) > MAX_ANSWER_CHARS:
        issues.append(f"çok uzun (>{MAX_ANSWER_CHARS} karakter)")
    return issues
