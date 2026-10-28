# ADR-002: LLM sağlayıcısı seçimi

- **Durum:** Önerildi, kullanıcı onayı bekleniyor (onay kapısı #2)
- **Tarih:** 2026-10-28

## Bağlam
Mülakatçı ve değerlendirici için Türkçe'de iyi, yapılandırılmış çıktı (JSON) verebilen ve
ücretsiz katmanı olan bir LLM gerekiyor. Gecikme hedefi: sesli yanıt p95 < 2,5 sn.

## Seçenekler
| | Gemini (ör. Flash) | Groq (ör. Llama 3.3 70B) |
|---|---|---|
| Ücretsiz kota | Proje başına günlük/dakikalık limit; 2026'da düşürüldüğüne dair raporlar var | Organizasyon başına RPM/RPD + token/dk limiti |
| Hız | İyi | Çok iyi (LPU) |
| Türkçe kalite | Henüz ölçülmedi | Henüz ölçülmedi |
| Ek fayda | — | Aynı hesapla Whisper STT |
| Gizlilik | Ücretsiz katman verisi model geliştirmede kullanılabilir | Gizlilik sayfasında belirtilecek |

Kota rakamları üçüncü taraf kaynaklarda tutarsız; kesin değerler anahtar alındıktan sonra
sağlayıcı konsolundan doğrulanacak.

## Karar
Bekliyor. `services/api/scripts/compare_llm.py` iki sağlayıcıda aynı 4 Türkçe görevi
(ilan → JSON, açılış sorusu, takip sorusu, prompt injection direnci) çalıştırıp
`evals/reports/llm-comparison.md` raporunu üretir. Karar bu rapora göre verilecek.

## Sonuçlar
Karar sonrası doldurulacak.
