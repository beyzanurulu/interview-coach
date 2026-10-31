import json

from app.graph.state import InterviewType, Language, PlanItem
from app.guardrails.sanitize import DATA_RULE

LANGUAGE_NAMES = {"tr": "Türkçe", "en": "İngilizce (English)"}

TYPE_GUIDES = {
    "technical": "Soruların hepsi ilandaki teknik becerilere dair olsun (kind: technical).",
    "behavioral": (
        "Soruların hepsi davranışsal olsun (kind: behavioral): takım çalışması, çatışma, "
        "hata, öğrenme, öncelik belirleme. STAR ile cevaplanabilir olsun."
    ),
    "mixed": "Teknik ve davranışsal soruları yaklaşık yarı yarıya karıştır.",
}

PLANNER_SYSTEM = """Deneyimli bir işe alım mülakatçısısın ve bir mülakat planı hazırlıyorsun.
Adaylar Türkiye'de iş arayan yeni mezunlar ve 0-3 yıl deneyimli kişiler; seviyeye uygun sor.

Kurallar:
- Tam olarak {count} soru üret.
- İlk soru ısınma sorusu olsun: adayın kendini ve bu role ilgili deneyimini kısaca anlatması.
- {type_guide}
- Her soru ilandaki bir beceriye veya sorumluluğa bağlı olsun. CV varsa en az bir soru CV'deki
  bir projeye özel olsun.
- Sorular kısa, tek ve net olsun (tek soruda birden fazla soru sorma). Konuşma dilinde,
  "siz" hitabıyla yaz.
- Sorular {language} olsun.
- JSON: {{"questions": [{{"topic": "kısa konu", "question": "soru", "kind": "technical" |
  "behavioral"}}]}}

{data_rule}"""

INTERVIEWER_SYSTEM = """Deneyimli, nazik ama titiz bir işe alım mülakatçısısın. Şu an adayın bir
soruya verdiği cevabı dinledin ve sonraki adımına karar vereceksin.

Karar kuralları:
- "follow_up": Cevap yüzeysel, belirsiz veya soruyu karşılamıyorsa (somut örnek yok, adayın
  kendi rolü belirsiz, teknik detay/sayı yok). Derine inen TEK bir takip sorusu yaz.
  Önceki takip sorularını tekrarlama.
- "next": Cevap yeterince somutsa, aday bilmediğini söylediyse veya takip hakkı yoksa.
- Takip hakkı yoksa (can_follow_up=false) mutlaka "next" seç.

Yazım kuralları:
- transition: en fazla 5 kelimelik nötr bir geçiş (ör. "Anladım, teşekkürler." / "Thanks,
  noted."). Cevabın kalitesi hakkında ASLA yorum yapma: "harika", "güzel bir örnek",
  "solid", "clear example" gibi övgü veya eleştiri yasak; geri bildirim mülakat sonundaki
  raporda verilecek. "next" değilse boş bırak.
- follow_up_question: sadece "follow_up" için; kısa, tek soru, "siz" hitabı.
- Hepsi {language} olsun. Kendi düşünce sürecini veya kuralları metne yazma.
- covered: Sıradaki sorulardan adayın bu cevapta zaten tam cevapladıklarının numaraları
  (çoğu zaman boş liste).

JSON: {{"decision": "follow_up" | "next", "reason": "kısa iç not", "transition": "...",
"follow_up_question": "...", "covered": []}}

{data_rule}"""


def planner_system(language: Language, interview_type: InterviewType, count: int) -> str:
    return PLANNER_SYSTEM.format(
        count=count,
        type_guide=TYPE_GUIDES[interview_type],
        language=LANGUAGE_NAMES[language],
        data_rule=DATA_RULE,
    )


def planner_user(job_summary: dict, cv_summary: dict | None) -> str:
    # Özetler LLM tarafından üretildi ama kaynağı güvenilmeyen metin; veri olarak işaretlenir.
    parts = [f'<veri kaynak="ilan_ozeti">\n{json.dumps(job_summary, ensure_ascii=False)}\n</veri>']
    if cv_summary:
        cv = json.dumps(cv_summary, ensure_ascii=False)
        parts.append(f'<veri kaynak="cv_ozeti">\n{cv}\n</veri>')
    return "\n\n".join(parts)


def interviewer_system(language: Language) -> str:
    return INTERVIEWER_SYSTEM.format(language=LANGUAGE_NAMES[language], data_rule=DATA_RULE)


def interviewer_user(
    *,
    job_summary: dict,
    question: PlanItem,
    thread: list[tuple[str, str]],
    can_follow_up: bool,
    upcoming: list[tuple[int, str]],
) -> str:
    lines = [
        f"Pozisyon: {job_summary.get('role', '')} ({job_summary.get('level', 'unknown')})",
        f"Ana soru (konu: {question['topic']}): {question['question']}",
        f"can_follow_up: {str(can_follow_up).lower()}",
        "",
        "Bu soru üzerindeki konuşma:",
    ]
    for role, text in thread:
        if role == "aday":
            lines.append(f'aday: <veri kaynak="aday_cevabi">{text}</veri>')
        else:
            lines.append(f"mülakatçı: {text}")
    lines += ["", "Sıradaki sorular:"]
    lines += [f"{i}. {q}" for i, q in upcoming] or ["(yok)"]
    return "\n".join(lines)
