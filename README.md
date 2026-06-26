# Batı Antalya Tarımsal Kalkınma Rehberi (Agri-DSS)

[![Durum](https://img.shields.io/badge/durum-prototip-green.svg)](https://tarimsalkoridor.online)
[![Mimari](https://img.shields.io/badge/mimari-statik_site-blue.svg)](#mimari)

Batı Antalya (Demre, Finike, Kaş, Kemer, Kumluca) koridorundaki çiftçiler ve tarım
yatırımcıları için **veri-odaklı bir Karar Destek Sistemi (Decision Support System – DSS)**.

**Canlı site:** https://tarimsalkoridor.online

---

## 1. Amaç ve Çözülen Problem

### Problem: "Ortakların Trajedisi"
Çiftçilerin birbirinden habersiz şekilde o an kârlı görünen ürüne (örn. domates) yönelmesi,
hasat döneminde arz fazlasına, fiyatların maliyetin altına düşmesine ve çiftçinin zarar
etmesine yol açar.

### Çözüm: Veri-Odaklı Koordinasyon
Sistem, her mahalle/parsel için kârlılığı optimize edecek ürünü önermeyi hedefler. Yalnızca
toprağı ve iklimi değil; tahmini pazar fiyatlarını ve bölgedeki diğer üreticilerin
eğilimlerini de (gelecek faz) dikkate alır.

---

## 2. Özellikler

- **Dinamik bölge seçimi:** İlçe → Mahalle bazında filtreleme (5 ilçe, 147 mahalle).
- **Sezonluk tavsiyeler:** Seçilen bölge için en uygun topraklı tarım ürünleri; her ürün için
  tahmini verim, tahmini kârlılık ve agronomik/ekonomik gerekçe.
- **Uzun vadeli yatırım tavsiyesi:** Bölgenin iklim ve arazi yapısına uygun ağaç/fidan önerisi
  (avokado, zeytin, nar, badem, Finike portakalı vb.).
- **Kavramsal pazar analizi:** Bölge için olası pazar açığı / fırsat öngörüsü.
- **Yazdırılabilir rapor:** Analiz sonucu, muhtarlık panoları veya kooperatifler için A4
  formatında yazdırılabilir.

---

## 3. Mimari

Sistem **tamamen istemci-taraflı (client-side) statik bir sitedir** — sunucu/backend gerekmez.
Bu sayede GitHub Pages gibi statik barındırma üzerinde doğrudan çalışır.

```
index.html   → Arayüz + tüm DSS mantığı (Tailwind CDN, vanilla JS)
data.json    → Veri katmanı (kod ile veri ayrıdır)
CNAME        → Özel alan adı (tarimsalkoridor.online)
```

### Veri formatı (`data.json`)
Veri, tekrarsız (DRY) bir yapıda tutulur:

- `cropSets` — yeniden kullanılan sezonluk ürün setleri (ör. `seraDomatesBiberSalatalik`).
- `longTermCrops` — uzun vadeli yatırım ürünleri sözlüğü (ör. `avokado`, `zeytin`).
- `regions` — İlçe → Mahalle → kayıt. Her kayıt:
  - `cropSet` (set referansı) **veya** `crops` (satır içi özel liste)
  - `longTerm` (referans) **veya** `longTermCustom` (satır içi özel ürün)
  - `marketGap` (kavramsal pazar açığı metni)

`index.html`, açılışta `data.json`'u `fetch` ile yükler ve bu referansları çözer.
**Veriyi güncellemek için yalnızca `data.json` düzenlenir; koda dokunmak gerekmez.**

---

## 4. Yerel Çalıştırma

`data.json` `fetch` ile yüklendiği için dosyayı çift tıklamak (`file://`) yerine basit bir
web sunucusu kullanın:

```bash
# Repo kökünde:
python3 -m http.server 8000
# Tarayıcıda: http://localhost:8000
```

---

## 5. Yayınlama (GitHub Pages)

1. Depoyu GitHub'a gönderin (`main` dalı).
2. **Settings → Pages → Source: Deploy from a branch → `main` / `root`**.
3. `CNAME` dosyası `tarimsalkoridor.online` alan adını bağlar; DNS kayıtlarının GitHub
   Pages'e yönlendirildiğinden emin olun.

Build adımı yoktur — `index.html` ve `data.json` doğrudan yayınlanır.

---

## 6. Veri Notu

Mevcut veriler, bölgesel raporlara (ekonomi, çevre, arazi kullanımı, iklim) dayalı
**kavramsal verilerdir**. İleride gerçek toprak/iklim/pazar veri kaynaklarıyla
`data.json` değiştirilerek sistem üretim moduna taşınabilir.

---

## 7. Lisans

Bu proje **Apache-2.0** lisansı ile yayınlanmıştır. Ayrıntılar için depodaki
[`LICENSE`](./LICENSE) dosyasına bakın.
