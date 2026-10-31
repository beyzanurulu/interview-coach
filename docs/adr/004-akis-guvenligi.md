# ADR-004: Mülakat akışının gerçekçiliği ve sapmaya karşı koruma

- **Durum:** Kabul edildi (ürün kararları kullanıcı onayıyla: 2026-10-31)
- **Tarih:** 2026-10-31

## Bağlam
LLM'ler zaman zaman konudan sapar, bilgi uydurur veya kuralları unutur; kullanıcılar da mülakat
ekranını başka amaçlarla kullanmaya çalışabilir (sohbet, ödev, cevap isteme, trol). Ürünün gerçek
bir mülakat deneyimi sunması ve ücretsiz kotanın amacı dışında harcanmaması gerekiyor.

## Karar
**İlke: akışı kod yönetir; model sınıflandırır ve kısa metin üretir; üretilen metin kodla denetlenir.**

1. **Aşama iskeleti (kodla):** ısınma → deneyim → teknik/davranışsal → "bize sormak istediğiniz bir
   şey var mı?" Plan çıktısı sıralanır; ısınma yoksa şablon eklenir; tekrar eden, çoklu soru içeren,
   yanlış dilde veya CV yüklenmemişken CV'den bahseden sorular atılır.
2. **Aday soruları aşaması:** son ~90 sn'ye veya plan bitince girilir; en fazla 2 soru. Cevap
   yalnızca ilandan çıkarılan bilgiye dayanır (konum, çalışma modeli, yan haklar dahil); bilgi
   yoksa "İK ekibimiz dönüş yapacak" şablonu. Model hata verirse nötr bir cevapla kapanır.
3. **Mesaj türü sınıflandırması:** cevap, açıklama isteme, bilmiyorum, cevap isteme, konu dışı,
   yapay zekâ sorusu, uygunsuz, anlaşılmayan. Cevap dışındaki türlere **sabit şablonla** yanıt
   verilir ve soru tekrarlanır; takip hakkından düşmez. Kısa ve net mesajlar ("örnek cevap söyler
   misin", "bot musun", "bilmiyorum") kural tabanlı tanınır; bu durumda LLM çağrılmaz.
4. **Tekrarlanan konu dışı / uygunsuz davranış:** daha net bir uyarı verilir, **mülakat
   sonlandırılmaz** (ürün kararı: uyarıyla devam).
5. **Çıktı denetimi:** her mülakatçı metni övgü/değerlendirme, işe alım vaadi, yanlış dil,
   sistem iç terimleri ("ilan özeti", "mevcut veriler"), uzunluk ve birden fazla soru açısından
   kontrol edilir. Geçemezse model sorunlar gösterilerek bir kez daha denenir; yine geçemezse
   güvenli şablona veya plandaki hazır soruya düşülür.

## Seçenekler (değerlendirilen)
- Sadece prompt ile kural koymak: ucuz ama modelin uyacağı garanti değil (simülasyonda övgü ve
  "ilanda yer almıyor" gibi sızıntılar görüldü).
- Ayrı bir "denetçi" LLM çağrısı: daha esnek ama tur başına gecikme ve kota maliyeti ikiye katlanır.
- Model eğitimi (fine-tuning): kapsam dışı; veri yok.

## Sonuçlar
- `evals/interviews/tr-adversarial.json` senaryosu (konu dışı, açıklama isteme, cevap isteme,
  yapay zekâ sorusu, uygunsuz dil, anlaşılmayan mesaj, bilmiyorum, yanlış dil) gerçek modelle
  çalıştırılıp otomatik kontrol edilir; sonuç `evals/reports/simulation-tr-adversarial.md`.
- Model deterministik olmadığı için tek çalıştırma kanıt değildir; Aşama 3'te çoklu çalıştırma
  ve oran raporu eklenecek.
- Groq ücretsiz katmanında model başına **günlük 200.000 token** sınırı var (2026-10-31'de hata
  mesajından okundu). Simülasyonlar bu kotayı hızla tüketir; canlı kullanıcılarla paylaşıldığı
  için kapasite planlaması gerekiyor (bkz. ADR-002 sonuçları).
