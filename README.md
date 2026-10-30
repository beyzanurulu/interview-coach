# interview-coach

İş ilanına göre **sesli** mülakat pratiği yaptıran ve sonunda rapor veren bir koç.
Hedef kitle: Türkiye'de iş arayan yeni mezunlar ve 0–3 yıl deneyimli adaylar (TR / EN).

> **Durum:** Aşama 0 (kurulum). Şu an çalışan tek şey boş bir frontend sayfası ve backend'de `/health` uç noktası.

## Şu an olanlar
- Monorepo iskeleti: `apps/web` (Next.js 15, TypeScript, Tailwind), `services/api` (FastAPI, Python 3.12, uv)
- Backend: `/health` uç noktası + test
- CI (GitHub Actions): ruff, pytest, eslint, tsc, vitest, Next.js build
- pre-commit: ruff, eslint, sır kontrolü
- LLM karşılaştırma scripti (`services/api/scripts/compare_llm.py`)

## Yol haritası
Metin tabanlı mülakat çekirdeği (LangGraph) → ses (VAD, STT, TTS, barge-in) → değerlendirme ve rapor →
üyelik, kota, KVKK → panel → canlıya alma → dokümantasyon. Ayrıntılar `docs/adr/` altında.

## Yerel geliştirme

```bash
cp .env.example .env
```

Backend:

```bash
cd services/api && uv sync && uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd apps/web && npm install && npm run dev
```

Testler:

```bash
cd services/api && uv run pytest
```

```bash
cd apps/web && npm test
```

## Mimari kararlar
- [ADR-001: Genel mimari](docs/adr/001-mimari.md)
- [ADR-002: LLM sağlayıcısı](docs/adr/002-llm-saglayici.md): Groq `qwen/qwen3.8-27b`
