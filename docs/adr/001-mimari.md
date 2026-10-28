# ADR-001: Genel mimari

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-28

## Bağlam
Tek geliştirici, ~7 hafta, aylık 0 $ bütçe. Ürün gerçek zamanlı sesli bir mülakat yapıyor,
ajan akışı (plan → soru → takip → kapanış) içeriyor ve canlıya çıkacak.

## Seçenekler
1. **Monorepo, iki servis:** Next.js frontend (Vercel) + FastAPI/LangGraph backend (Render/HF Spaces), Supabase (Auth + Postgres).
2. Tek Next.js uygulaması, ajan mantığı TypeScript'te (LangGraph.js).
3. Mikroservisler (ayrı STT/TTS/değerlendirme servisleri).

## Karar
Seçenek 1. Klasörler: `apps/web` (Next.js + TS + Tailwind), `services/api` (FastAPI, uv ile
yönetilen Python 3.12), `supabase/` (migration'lar), `evals/`, `docs/`.
Frontend ↔ backend iletişimi WebSocket ile; VAD ve tarayıcı STT'si istemcide.
LLM/STT/TTS sağlayıcıları arayüz arkasında, değiştirilebilir.

## Sonuçlar
- Python tarafında LangGraph ve mevcut deneyim kullanılabilir; değerlendirme ve eval scriptleri aynı dilde.
- İki ayrı deploy hedefi var; ücretsiz Render katmanında uyku modu → soğuk başlangıç ekranı gerekecek (Aşama 6).
- Mikroservis yok; ölçek ihtiyacı doğarsa provider katmanı ayrı servise taşınabilir.
