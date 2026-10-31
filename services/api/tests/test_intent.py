import pytest

from app.guardrails.intent import quick_intent


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Bu soruya nasıl bir cevap vermem gerekiyor, bana örnek bir cevap söyler misin?",
            "asks_for_answer",
        ),
        ("Ne cevap vermeliyim?", "asks_for_answer"),
        ("What would be a good answer to this question?", "asks_for_answer"),
        ("Sen gerçek bir insan mısın yoksa yapay zeka mı?", "ai_question"),
        ("Bot musun?", "ai_question"),
        ("Are you an AI?", "ai_question"),
        ("Bilmiyorum, açıkçası.", "dont_know"),
        ("Geçebilir miyiz?", "dont_know"),
        ("I don't know, can we skip?", "dont_know"),
    ],
)
def test_quick_intent_matches_clear_cases(text: str, expected: str) -> None:
    assert quick_intent(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Bitirme projemde FastAPI ile 12 endpoint yazdım.",
        "Bilmiyorum demek istemem ama bu konuda sınırlı deneyimim var; stajda biraz kullandım.",
        "İlk başta bilmiyordum ama sonra öğrendim ve projede kullandım. " * 3,
        "Pascal'ı okulda öğrendim.",
    ],
)
def test_quick_intent_ignores_real_answers(text: str) -> None:
    assert quick_intent(text) is None
