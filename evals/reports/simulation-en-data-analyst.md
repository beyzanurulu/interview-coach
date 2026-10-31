# Simülasyon: en-data-analyst

Model: `qwen/qwen3.8-27b`

## Otomatik kontroller

| Kontrol | Sonuç |
|---|---|
| Mülakat düzgün kapandı | ✅ (completed) |
| Aday soruları aşamasına gelindi | ✅ |
| Çıktı kuralı ihlali (övgü, işe alım ifadesi, yanlış dil) | ✅ yok |

## Özet

- Plan soru sayısı: 3
- Takip sorusu sayısı: 1
- Yönlendirme sayıları: {}
- Mülakatçı tur gecikmesi (metin): p50 3.60 sn, p95 9.90 sn, n=6

Notlar: Gecikmeye sağlayıcı kota (429) beklemeleri dahildir; aday simülasyonu da aynı
kotayı kullanır. Simülasyon gerçek zamanı beklemez; süre sınırı devreye girmez.

## İlan özeti

```json
{
  "role": "Junior Data Analyst",
  "level": "junior",
  "skills": [
    "SQL",
    "Excel",
    "Power BI veya Tableau",
    "Teknik olmayan paydaşlara içgörü açıklama"
  ],
  "nice_to_have": [
    "Python (pandas)"
  ],
  "responsibilities": [
    "Veri analizi yapma",
    "Görselleştirmeler (dashboard) oluşturma",
    "İçgörüleri teknik olmayan paydaşlara aktarma"
  ]
}
```

## Transkript

**Mülakatçı (soru 1):** Hi, welcome! We'll have an interview of about 5 minutes for the Junior Data Analyst position. If you're ready, let's begin. Can you briefly introduce yourself and explain why you are interested in this Junior Data Analyst role?

**Aday (detailed):** I recently graduated with a degree in Industrial Engineering and spent the last six months interning in retail analytics, where I built a weekly sales dashboard in Power BI that reduced the reporting preparation time by 15%. I am eager to join your team because I love translating raw data into actionable business insights, a skill I successfully demonstrated during my internship. This role offers the perfect opportunity to apply my technical foundation and drive efficiency in a larger, more complex data environment.

**Mülakatçı (soru 2):** Thanks, noted. Tell me about a specific project where you used SQL or Excel to analyze data and generate a dashboard or insight.

**Aday (shallow):** Yeah, so I did some stuff with SQL during my internship, I guess. It was... yeah, just a dashboard thing.

**Mülakatçı (takip):** Could you please specify what the dashboard was tracking and what specific insight you derived from the data?

**Aday (detailed):** During my internship, I designed a Power BI dashboard that tracked weekly sales performance by store, category, and promotional activity for our retail client. I noticed a significant discrepancy where high-volume categories consistently underperformed during non-promotional weeks compared to their historical averages. By isolating this trend, I identified that a specific 15% drop in sales was directly correlated with a supply chain delay reducing stock availability by 20%. This insight allowed the analytics team to present a data-backed case to operations for earlier inventory ordering, which subsequently improved stock availability and stabilized weekly revenue.

**Mülakatçı (soru 3):** Thanks, noted. Describe a time when you had to explain a complex data finding to a non-technical stakeholder who did not understand the initial result.

**Aday (detailed):** During my internship at the retail company, I discovered a 15% drop in weekly sales for a specific product category, but the initial dashboard chart confused our regional manager who thought it indicated a data error. I simplified the narrative by creating a single-line trend comparison showing that the drop coincided exactly with a competitor’s major promotional campaign, rather than a systemic inventory issue. By framing the data as a market reaction rather than a technical anomaly, he immediately understood the external driver and authorized a targeted counter-promotion that recovered 80% of the lost revenue within two weeks.

**Mülakatçı (aday soruları):** Thanks, noted. That's all from my side. Before we wrap up, is there anything you'd like to ask us?

**Aday (ask_known):** Which dashboard tool does the team mainly use?

**Mülakatçı (adaya cevap):** The role involves working with either Power BI or Tableau, so you will likely gain experience with one or both depending on the team's current projects. For specific details on the primary tool, our HR team can provide more information. Is there anything else you'd like to ask?

**Aday (no_question):** No, I don't have any questions right now, thank you.

**Mülakatçı (kapanış):** That brings us to the end. Thank you for your time, and best of luck!
