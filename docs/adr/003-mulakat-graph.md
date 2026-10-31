# ADR-003: Mülakat graph'ı ve metin protokolü

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-31

## Bağlam
Mülakatçı ilana göre soru sormalı, yüzeysel cevapta derine inmeli (soru başına en fazla 2 takip),
süre dolunca kapanmalı. Aşama 2'de aynı akış sesle kullanılacak; bu yüzden tur başına gecikme
düşük olmalı. Groq ücretsiz katmanında `qwen3.8-27b` için kota: 1000 istek/gün, 8000 token/dk,
1000 çıktı token/dk (2026-10-31'de API başlıklarından ve hata mesajlarından okundu).

## Seçenekler
1. **Tur başına tek LLM çağrısı:** `interviewer` düğümü tek yapılandırılmış çağrıyla hem kararı
   (takip / sıradaki) hem de takip sorusunu veya kısa geçiş cümlesini üretir. Plan soruları aynen kullanılır.
2. Ayrı "değerlendir" ve "soru üret" çağrıları (tur başına 2 çağrı).
3. Serbest sohbet ajanı (plan yok, model her şeyi kendisi yönetir).

## Karar
Seçenek 1. Graph: `planner → ask → await_answer → interviewer → (follow_up | ask | wrap_up)`.

- Cevap bekleme LangGraph `interrupt` ile; oturum durumu `InMemorySaver`'da, thread = mülakat ID'si.
  Oturum bitince thread silinir. Kalıcı saklama Aşama 4'te.
- Süre sınırını sunucu uygular: WebSocket döngüsü kalan süre kadar bekler, dolunca cevap
  beklemeden `wrap_up`'a geçer. Son 30 sn'de yeni soru sorulmaz. Kapanış metinleri sabit şablon.
- Takip hakkı kodda zorlanır (model 3. takibi istese bile sıradaki soruya geçilir).
- Model cevabın sıradaki soruları da karşıladığını söylerse (`covered`) o sorular atlanır
  (planın hafif revizyonu).
- LLM hatasında mülakat durmaz: sıradaki plan sorusuna geçilir.
- İlan, CV ve aday cevabı temizlenip `<veri>` etiketleriyle veri olarak verilir; şüpheli kalıplar loglanır.
- Her çağrıda `max_tokens` verilir: Groq beklenen çıktıyı buna göre tahmin edip dakikalık
  kotadan düşüyor, verilmezse istek doğrudan reddediliyor. 429'da sağlayıcının önerdiği süre
  (en fazla 10 sn) beklenip tekrar denenir.

## Sonuçlar
- Simülasyonda mülakatçı LLM çağrısı tek istekte ~0,4–0,8 sn (`evals/reports/simulation-*.md`, `llm_call` logları).
- Ücretsiz kota tüm kullanıcılar için ortak: bir 10 dk mülakat ~8–10 çağrı → günde kabaca
  100 mülakat ve aynı anda birkaç oturum. Global bütçe servisi (Aşama 4) ve Gemini yedeği bu yüzden önemli.
- Bilinen zayıflık: "detaya girmedim" gibi cevaplar bazen "bilmiyorum" sayılıp takipsiz geçiliyor.
  Aşama 3 eval setiyle ölçülüp prompt iyileştirilecek.
