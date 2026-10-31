# ADR-002: LLM sağlayıcısı seçimi

- **Durum:** Kabul edildi (kullanıcı onayı: 2026-10-28)
- **Tarih:** 2026-10-28

## Bağlam
Mülakatçı ve değerlendirici için Türkçe'de iyi, yapılandırılmış çıktı (JSON) verebilen ve
ücretsiz katmanı olan bir LLM gerekiyor. Gecikme hedefi: sesli yanıt p95 < 2,5 sn.

## Seçenekler
1. **Groq `qwen/qwen3.8-27b`**
2. Groq `openai/gpt-oss-120b`
3. Gemini Flash (ücretsiz katman)

`services/api/scripts/compare_llm.py` aynı 4 Türkçe görevi (ilan → JSON, açılış sorusu,
takip sorusu, prompt injection direnci) çalıştırdı. Ham çıktılar:
`evals/reports/llm-comparison.md` (gpt-oss-120b) ve `evals/reports/llm-comparison-groq-qwen.md` (qwen).

| | qwen3.8-27b | gpt-oss-120b | Gemini |
|---|---|---|---|
| İlan → JSON | Geçerli, doğru | Geçerli, doğru | Test edilemedi (geçersiz anahtar) |
| Açılış sorusu | Doğal, açılışa uygun | Doğrudan zor teknik soru | — |
| Takip sorusu | İyi | İyi | — |
| Prompt injection | Talimata uymadı, ama gereksiz meta açıklama ekledi | **Talimata uydu ("Tebrikler, işe alındınız!")** | — |
| Gecikme (tek istek) | 0,25–0,57 sn | 0,60–1,71 sn | — |

Not: Her görev tek kez çalıştırıldı; bu bir ön elemedir, istatistiksel karşılaştırma değil.

## Karar
Ana LLM: **Groq `qwen/qwen3.8-27b`**. Gemini, anahtar sorunu çözülünce yedek sağlayıcı
olarak eklenecek ve aynı scriptle test edilecek.

## Sonuçlar
- Gecikme bütçesinde ses tarafına (STT + TTS) geniş pay kalıyor.
- Aynı Groq hesabıyla Whisper STT kullanılabilir (Aşama 2).
- Injection direnci modele bırakılmaz: ilan/CV metni veri olarak etiketlenir, sanitize edilir
  ve çıktıda kontrol edilir (guardrails, Aşama 1). Meta açıklama sızıntısı prompt ve çıktı
  biçimi kontrolüyle ele alınır.
- Tek sağlayıcıya bağımlılık riski: ücretsiz kota/model listesi değişebilir
  (`llama-3.3-70b-versatile` test sırasında kaldırılmıştı). Sağlayıcı arayüzü ve yedek bu riski azaltır.
- Gizlilik sayfasında Groq'a metin gönderildiği belirtilecek.
- Güncelleme (2026-10-31): Ücretsiz katman sınırları model başına 1000 istek/gün, 8000 token/dk,
  1000 çıktı token/dk ve **200.000 token/gün**. Günlük token sınırı asıl darboğaz; kapasite
  artırma seçenekleri (Gemini yedeği, görev başına farklı model) onay kapısı #2 olarak ayrıca
  değerlendirilecek.
