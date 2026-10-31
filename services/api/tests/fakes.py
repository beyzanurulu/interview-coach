import json
from collections.abc import Callable

from app.providers.llm.base import LLMError, Message

Handler = Callable[[list[Message]], str | dict]


class FakeLLM:
    """`purpose` başına yanıt üreten sahte sağlayıcı. Yanıt str, dict (JSON'a çevrilir)
    veya bunları üreten fonksiyon olabilir; liste verilirse sırayla tüketilir."""

    name = "fake"

    def __init__(self, responses: dict[str, object]):
        self.responses = {k: list(v) if isinstance(v, list) else v for k, v in responses.items()}
        self.calls: list[tuple[str, list[Message]]] = []

    async def complete(
        self, messages, *, purpose, json_mode=False, temperature=0.3, max_tokens=None
    ):
        self.calls.append((purpose, messages))
        response = self.responses.get(purpose)
        if isinstance(response, list):
            response = response.pop(0) if response else None
        if callable(response):
            response = response(messages)
        if response is None:
            raise LLMError(f"fake: '{purpose}' için yanıt yok")
        return json.dumps(response, ensure_ascii=False) if isinstance(response, dict) else response

    def count(self, purpose: str) -> int:
        return sum(1 for p, _ in self.calls if p == purpose)


JOB_TEXT = (
    "Junior Backend Geliştirici. Python ve FastAPI ile REST servisleri geliştirecek, "
    "PostgreSQL ve Docker bilen, 0-2 yıl deneyimli takım arkadaşı arıyoruz."
)

JOB_SUMMARY = {
    "role": "Junior Backend Geliştirici",
    "level": "junior",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "nice_to_have": [],
    "responsibilities": ["REST servisleri geliştirmek"],
}


def make_plan(n: int, language: str = "tr") -> dict:
    stages = ["warmup", "experience"] + ["technical"] * max(0, n - 2)
    template = "Soru {i} için ne düşünürsünüz?" if language == "tr" else "What about topic {i}?"
    return {
        "questions": [
            {"topic": f"konu {i}", "question": template.format(i=i), "stage": stages[i]}
            for i in range(n)
        ]
    }


def q(i: int) -> str:
    return f"Soru {i} için ne düşünürsünüz?"


def decision(kind: str, **kw) -> dict:
    base = {"answer_type": "answer", "decision": kind, "transition": "", "follow_up_question": ""}
    if kind == "follow_up":
        base["follow_up_question"] = "Biraz daha somut anlatır mısınız?"
    if kind == "next":
        base["transition"] = "Anladım, teşekkürler."
    return {**base, **kw}


def classified(answer_type: str, **kw) -> dict:
    return {"answer_type": answer_type, "decision": None, **kw}


def candidate(kind: str, answer: str = "") -> dict:
    return {"type": kind, "answer": answer}


def minimal_pdf(text: str) -> bytes:
    """Tek sayfalık, metin içeren geçerli bir PDF üretir (test fixture'ı)."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return bytes(out)
