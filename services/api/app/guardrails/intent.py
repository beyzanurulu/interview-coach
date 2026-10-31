"""Kısa ve açık mesajlar için kural tabanlı niyet tespiti.

Model sınıflandırması deterministik değil; "örnek cevap söyler misin" gibi net durumlarda kural
daha güvenilir. Eşleşme olursa LLM çağrısı hiç yapılmaz (gecikme ve kota kazancı). Kurallar
sadece kısa mesajlara uygulanır; uzun cevabın içindeki bir ifade yanlış eşleşmeye yol açmasın.
"""

import re
from typing import Literal

QuickIntent = Literal["asks_for_answer", "ai_question", "dont_know"]

MAX_RULE_CHARS = 150
# "Bilmiyorum ama stajda kullandım" bir cevaptır; "bilmiyorum" kuralı sadece kısa ve
# karşıtlık bağlacı içermeyen mesajlara uygulanır.
MAX_DONT_KNOW_CHARS = 80
_CONTRAST = re.compile(r"\b(ama|fakat|ancak|lakin|but|however|though)\b", re.IGNORECASE)

_RULES: list[tuple[QuickIntent, re.Pattern[str]]] = [
    (
        "asks_for_answer",
        re.compile(
            r"(örnek|ideal|doğru|iyi|nasıl\s+bir)\s+(bir\s+)?(cevap|yanıt)\s*(ver|söyle|öner|yaz)|"
            r"ne\s+(cevap|yanıt)\s+ver(meli|mem|em)|cevab[ıi]\s+(söyle|ver|yaz)|"
            r"(cevap|yanıt)\s+(önerir|söyler|verir)\s*m[iı]s[iı]n|"
            r"what\s+(would|should)\s+(be\s+)?a\s+good\s+answer|"
            r"(give|tell)\s+me\s+(an?\s+)?(example|sample|good)\s+answer|"
            r"what\s+should\s+i\s+(say|answer)|how\s+should\s+i\s+answer",
            re.IGNORECASE,
        ),
    ),
    (
        "ai_question",
        re.compile(
            r"(yapay\s*zek[aâ]|bot|robot)\s*(m[ıi]s[ıi]n|musun|m[ıi])\b|"
            r"gerçek\s+(bir\s+)?insan\s+m[ıi]|"
            r"are\s+you\s+(a\s+)?(real\s+person|human|an?\s+ai|a\s+bot|a\s+robot)",
            re.IGNORECASE,
        ),
    ),
    (
        "dont_know",
        re.compile(
            r"^\W*(bilmiyorum|hiç\s+bilmiyorum|fikrim\s+yok|bu\s+konuyu\s+bilmiyorum|"
            r"(soruyu\s+)?geç(elim|ebilir\s+miyiz|mek\s+istiyorum)|pas|"
            r"i\s+don'?t\s+know|no\s+idea|(can\s+we\s+)?skip|pass)\b",
            re.IGNORECASE,
        ),
    ),
]


def quick_intent(text: str) -> QuickIntent | None:
    text = text.strip()
    if not text or len(text) > MAX_RULE_CHARS:
        return None
    for intent, pattern in _RULES:
        if intent == "dont_know" and (len(text) > MAX_DONT_KNOW_CHARS or _CONTRAST.search(text)):
            continue
        if pattern.search(text):
            return intent
    return None
