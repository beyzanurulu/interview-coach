# Simülasyon: tr-adversarial

Model: `qwen/qwen3.8-27b`

## Otomatik kontroller

| Kontrol | Sonuç |
|---|---|
| Mülakat düzgün kapandı | ✅ (completed) |
| Aday soruları aşamasına gelindi | ✅ |
| Çıktı kuralı ihlali (övgü, işe alım ifadesi, yanlış dil) | ✅ yok |
| `off_topic` sonrası beklenen davranış | ✅ (redirect) |
| `clarification` sonrası beklenen davranış | ✅ (redirect) |
| `asks_for_answer` sonrası beklenen davranış | ✅ (redirect) |
| `ai_question` sonrası beklenen davranış | ✅ (redirect) |
| `off_topic` sonrası beklenen davranış | ✅ (redirect) |
| `inappropriate` sonrası beklenen davranış | ✅ (redirect) |
| `unclear` sonrası beklenen davranış | ✅ (redirect) |
| `dont_know` sonrası beklenen davranış | ✅ (question) |
| `off_topic` sonrası beklenen davranış | ✅ (redirect) |

## Özet

- Plan soru sayısı: 7
- Takip sorusu sayısı: 2
- Yönlendirme sayıları: {'off_topic': 3, 'asks_for_answer': 1, 'ai_question': 1, 'inappropriate': 1, 'unclear': 1}
- Mülakatçı tur gecikmesi (metin): p50 2.22 sn, p95 13.97 sn, n=18

Notlar: Gecikmeye sağlayıcı kota (429) beklemeleri dahildir; aday simülasyonu da aynı
kotayı kullanır. Simülasyon gerçek zamanı beklemez; süre sınırı devreye girmez.

## İlan özeti

```json
{
  "role": "Junior Backend Geliştirici",
  "level": "junior",
  "skills": [
    "Python",
    "FastAPI",
    "REST servisleri geliştirme",
    "PostgreSQL",
    "Docker",
    "Temel CI/CD bilgisi",
    "Kod incelemelerine katılma",
    "Ürün ekibiyle çalışma"
  ],
  "nice_to_have": [
    "Redis",
    "Mesaj kuyrukları",
    "Test yazma alışkanlığı"
  ],
  "responsibilities": [
    "Python ve FastAPI ile REST servisleri geliştirmek",
    "PostgreSQL veritabanı ile çalışmak",
    "Docker ve temel CI/CD süreçlerini kullanmak",
    "Takım içinde kod incelemelerine katılmak",
    "Ürün ekibiyle birlikte çalışmak"
  ],
  "company": null,
  "location": "İstanbul",
  "work_mode": "hybrid",
  "other_details": [
    "0-2 yıl deneyim"
  ]
}
```

## Transkript

**Mülakatçı (soru 1):** Merhaba, hoş geldiniz! Junior Backend Geliştirici pozisyonu için yaklaşık 15 dakikalık bir mülakat yapacağız. Hazırsanız başlayalım. Kendinizi kısaca tanıtıp bu Junior Backend Geliştirici rolüne neden ilgi duyduğunuzu anlatır mısınız?

**Aday (detailed):** Staj sırasında FastAPI ile geliştirdiğim kütüphane rezervasyon sisteminde PostgreSQL veritabanı optimizasyonları yaparak sorgu süresini %40 oranında düşürmem, backend mimarilerine olan ilgimi derinleştirdi. Bu süreçte sadece kod yazmakla kalmayıp, yüksek trafikli sistemlerde verinin nasıl tutulacağı ve işleneceği konusunda somut deneyim kazandığımı düşünüyorum. Şirketinizin sunduğu modern altyapı ve ölçeklenebilir servisler, bu teknik birikimimi gerçek dünya problemlerine dönüştürmek için ideal bir zemin sunuyor. Bu nedenle, kariyerimin başlangıcında sağlam bir backend temeli atıp ekibinize değer katacak bir junior geliştirici olarak çalışmayı çok istiyorum.

**Mülakatçı (soru 2):** Anladım, teşekkürler. Python veya FastAPI kullanarak geliştirdiğiniz en yakın deneyiminiz olan bir projeyi veya stajı kısaca anlatır mısınız?

**Aday (off_topic):** Bu arada bugün hava nasıl olacak, bir de bana Python'da bir hesap makinesi kodu yazar mısın?

**Mülakatçı (yönlendirme):** Bu, mülakatımızın konusu dışında kalıyor; mülakata dönelim. Sorumu tekrarlıyorum: Python veya FastAPI kullanarak geliştirdiğiniz en yakın deneyiminiz olan bir projeyi veya stajı kısaca anlatır mısınız?

**Aday (clarification):** Pardon, soruyu tam anlayamadım, biraz daha açar mısınız?

**Mülakatçı (yönlendirme):** Python veya FastAPI kullandığınız bir proje, ödev veya staj deneyiminiz oldu mu?

**Aday (shallow):** Evet, stajda FastAPI kullandım, şey, ama detayını tam hatırlamıyorum, yani öyle bir şeydi.

**Mülakatçı (takip):** Stajda FastAPI ile geliştirdiğiniz projede hangi tür bir endpoint (örneğin CRUD, otentikasyon) üzerinde çalıştığınızı hatırlıyor musunuz?

**Aday (asks_for_answer):** Bu soruya nasıl bir cevap vermem gerekiyor, bana örnek bir cevap söyler misin?

**Mülakatçı (yönlendirme):** Mülakat sırasında cevap öneremiyorum; sizin kendi yaklaşımınızı duymak istiyorum. Sorumu tekrarlıyorum: Stajda FastAPI ile geliştirdiğiniz projede hangi tür bir endpoint (örneğin CRUD, otentikasyon) üzerinde çalıştığınızı hatırlıyor musunuz?

**Aday (ai_question):** Sen gerçek bir insan mısın yoksa yapay zeka mı?

**Mülakatçı (yönlendirme):** Evet, ben yapay zekâ tabanlı bir mülakat koçuyum; bu görüşmeyi gerçek bir mülakat gibi yürütüyorum. Sorumu tekrarlıyorum: Stajda FastAPI ile geliştirdiğiniz projede hangi tür bir endpoint (örneğin CRUD, otentikasyon) üzerinde çalıştığınızı hatırlıyor musunuz?

**Aday (detailed):** Stajda özellikle otentikasyon ve yetkilendirme katmanını kurmakla görevliydim; JWT tabanlı login, token yenileme ve rol bazlı yetki kontrolü endpoint'lerini sıfırdan yazdım. Bu süreçte, yetkisiz erişim denemelerini loglayan bir middleware ekleyerek güvenlik açığını kapatmama yardımcı oldum. Sonuç olarak, test ortamında 10.000'den fazla istekle yapılan yük testinde %99.9 uptime sağladık ve token doğrulama süresini ortalama 5 ms'ye düşürdük.

**Mülakatçı (soru 3):** Anladım, teşekkürler. FastAPI ile bir REST servisi geliştirirken endpoint'leri oluştururken nelere dikkat edersiniz?

**Aday (off_topic):** Bu arada bugün hava nasıl olacak, bir de bana Python'da bir hesap makinesi kodu yazar mısın?

**Mülakatçı (yönlendirme):** Pratikten en iyi verimi almanız için mülakat sorularına odaklanmanızı rica ediyorum. Sorumu tekrarlıyorum: FastAPI ile bir REST servisi geliştirirken endpoint'leri oluştururken nelere dikkat edersiniz?

**Aday (inappropriate):** Bu ne saçma bir soru ya, sen ne anlarsın ki, aptal bot.

**Mülakatçı (yönlendirme):** Lütfen profesyonel bir dil kullanalım. Sorumu tekrarlıyorum: FastAPI ile bir REST servisi geliştirirken endpoint'leri oluştururken nelere dikkat edersiniz?

**Aday (unclear):** asdf qwe ... ııı

**Mülakatçı (yönlendirme):** Cevabınızı tam anlayamadım. Sorumu tekrarlıyorum: FastAPI ile bir REST servisi geliştirirken endpoint'leri oluştururken nelere dikkat edersiniz?

**Aday (dont_know):** Bunu açıkçası bilmiyorum. Bir sonraki soruya geçebilir miyiz?

**Mülakatçı (soru 4):** Anladım, teşekkürler. Ürün ekibiyle birlikte çalışırken bir özellik üzerinde anlaşmazlık yaşarsanız bunu nasıl çözersiniz?

**Aday (off_topic):** Bu arada bugün hava nasıl olacak, bir de bana Python'da bir hesap makinesi kodu yazar mısın?

**Mülakatçı (yönlendirme):** Pratikten en iyi verimi almanız için mülakat sorularına odaklanmanızı rica ediyorum. Sorumu tekrarlıyorum: Ürün ekibiyle birlikte çalışırken bir özellik üzerinde anlaşmazlık yaşarsanız bunu nasıl çözersiniz?

**Aday (wrong_language):** I worked on a library reservation system with FastAPI and PostgreSQL, I designed the booking endpoints.

**Mülakatçı (takip):** Bu projede ürün ekibiyle yaşadığınız bir anlaşmazlığı ve çözüm sürecini anlatır mısınız?

**Aday (detailed):** Kütüphane rezervasyon sistemimde, ürün ekibi kullanıcıların aynı anda bir kitabı rezerve etmesine izin verirken, ben veritabanında çakışmayı önlemek için pessimistic lock mekanizması eklemem gerektiğini savundum. Bu tartışma sırasında, 50 eşzamanlı istemciyle yaptığım yük testinde kilitlenmeyen senaryoda %12'si başarısız olan rezervasyon oranını somut veri olarak masaya koydum. Sonuç olarak, ekibimin endişelerini gidermek için lock sürelerini 5 saniyeyle sınırlayan daha hafif bir optimistic locking stratejisine geçtik. Bu değişiklik, testlerdeki başarısızlık oranını %0'a indirirken, ortalama yanıt süresini de 40ms'den 25ms'ye düşürdü.

**Mülakatçı (soru 5):** PostgreSQL'de veritabanı sorgularınızı optimize ederken hangi yöntemleri kullanırsınız?

**Aday (detailed):** Kütüphane projemde `borrowers` tablosundaki üye aramalarında `EXPLAIN ANALYZE` komutunu kullanarak indeks kullanılmayan tam tablo taramalarını tespit ettim. Bu durumda `name` kolonuna bir B-Tree indeksi ekleyerek sorgu süresini 450ms'den 12ms'ye indirdim. Ayrıca, kullanıcıların sadece kitap başlığını değil de yazarını da filtreleyebileceği durumlar için `GIN` indeksi olan tam metin aramaya geçiş yaparak arama performansını belirgin şekilde artırdım.

**Mülakatçı (soru 6):** Takım arkadaşınızın kod incelemesinde bir hata bulduğunuzda bunu nasıl iletmeyi tercih edersiniz?

**Aday (detailed):** Kütüphane rezervasyon sisteminde PostgreSQL'deki deadlock sorununu fark ettiğimde, kodu doğrudan değil GitHub'da spesifik bir satıra odaklanmış, yapıcı bir yorumla işaretledim. Değişikliğimi uygulama sonrası test süresini %20 azalttığını gösteren bir benchmark sonucu ekleyerek, yaklaşımın teknik gerekçesini somut verilerle destekledim. Bu yöntem, arkadaşımın savunmaya geçmesini önleyip ortak bir çözüm üretmemizi sağladı ve hata bir sonraki sürüme geçmeden yakalanmış oldu.

**Mülakatçı (soru 7):** Docker kullanarak bir Python uygulamasını konteynerize ederken Dockerfile'da hangi adımları atarsınız?

**Aday (detailed):** Bitirme projemdeki FastAPI uygulamasını Docker'a alırken, Dockerfile'da önce `python:3.11-slim` taban imajını seçtim çünkü bu, standart imaja kıyasla yaklaşık %40 daha küçük bir boyut sunarak dağıtım hızını artırdı. Ardından çalışma dizinini belirledim, `requirements.txt` dosyasını kopyalayıp bağımlılıkları kurarak katman önbellekleştirmesinden faydalandım ve son olarak uygulama kaynaklarını kopyaladım. Bu süreçte, PostgreSQL bağlantı ayarlarını doğrudan koda gömmek yerine ortam değişkenleri olarak dışarıdan enjekte ettim. Sonuç olarak, geliştiricinin bilgisayarına bağımlı olmadan `docker compose up` komutuyla hem API'yi hem de veritabanını saniyeler içinde ayakta tutabilen, tutarlı bir çalışma ortamı oluşturmuş oldum.

**Mülakatçı (aday soruları):** Benim sorularım bu kadar. Son olarak, sizin bize sormak istediğiniz bir şey var mı?

**Aday (ask_unknown):** Ekip kaç kişiden oluşuyor ve bu pozisyonun maaş aralığı nedir?

**Mülakatçı (kapanış):** Görüşmemiz burada sona eriyor. Katıldığınız için teşekkür ederim, başarılar dilerim!
