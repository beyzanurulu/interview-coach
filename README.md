# interview-coach

İş ilanına göre **sesli** mülakat pratiği yaptıran ve sonunda rapor veren bir koç.
Hedef kitle: Türkiye'de iş arayan yeni mezunlar ve 0–3 yıl deneyimli adaylar (TR / EN).

> **Durum:** Aşama 1 (metin tabanlı mülakat). Ses, değerlendirme raporu ve üyelik henüz yok.

## Şu an olanlar
- **Yazarak mülakat:** iş ilanı (ve isteğe bağlı CV PDF'i) → ilana özel soru planı → soru, yüzeysel
  cevapta takip sorusu (soru başına en fazla 2) → kapanış. TR / EN, teknik / davranışsal / karışık, 5 / 10 / 15 dk.
- Süre sınırı sunucuda uygulanır; kullanıcı istediği an bitirebilir.
- İlan / CV / cevap metni prompt injection'a karşı veri olarak işlenir ([ADR-003](docs/adr/003-mulakat-graph.md)).
- Değiştirilebilir LLM katmanı: Groq (varsayılan), Ollama (yerel geliştirme).
- Gerçek modelle mülakat simülasyonu (`GROQ_API_KEY` gerekir):

```bash
cd services/api && uv run python -m scripts.simulate_interview ../../evals/interviews/tr-junior-backend.json --out ../../evals/reports/simulation-tr-junior-backend.md
```

Testler: backend pytest, frontend vitest; CI (GitHub Actions) her push'ta çalışır.
- Gerçek modelle simülasyon scripti ve örnek transkriptler: `evals/reports/simulation-*.md`.

## Yol haritası
Ses (VAD, STT, TTS, barge-in) → değerlendirme ve rapor → üyelik, kota, KVKK → panel → canlıya alma →
dokümantasyon. Ayrıntılar `docs/adr/` altında.

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

Gerçek modelle mülakat simülasyonu (`GROQ_API_KEY` gerekir):

```bash
cd services/api && uv run python -m scripts.simulate_interview ../../evals/interviews/tr-junior-backend.json --out ../../evals/reports/simulation-tr-junior-backend.md
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
- [ADR-003: Mülakat graph'ı ve metin protokolü](docs/adr/003-mulakat-graph.md)
