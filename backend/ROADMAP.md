# Agri-DSS Backend — Yol Haritası

> **Strateji: Sözleşme Öncelikli (Contract-First).**
> Elimizde veri olmaması bir engel değil. Elimizde bir **veri sözleşmesi** var: `data.json`.
> Backend'i bu sözleşmeyi birebir koruyacak şekilde kurarız; bugün mevcut "kavramsal"
> veriyi servis eder, gerçek veri geldiğinde sadece veritabanını doldururuz — **kod değişmez,
> frontend değişmez.**

---

## Neden şimdi backend kurmak mantıklı?

| Soru | Cevap |
|------|-------|
| Veri yokken backend boşuna mı? | Hayır. Mevcut `data.json` **seed (tohum) veri** olur. Sistem ilk günden ayakta ve test edilebilir. |
| Frontend'i kırar mıyız? | Hayır. Backend, frontend'in beklediği JSON'un **aynısını** `/api/v1/data`'dan döndürür. |
| Mekansal (harita) veri sonra gelirse? | Şema bugünden hazır: `geometry` sütunları **boş (nullable)** açılır, veri gelince doldurulur. |
| Ne zaman gerçek veriye geçeriz? | İstediğin zaman. Geçiş = veritabanını doldurmak; uygulama mantığı sabit kalır. |

**Kısacası:** boş bir iskelet değil, *bugünkü veriyle çalışan ama yarının verisine hazır* bir backend kuruyoruz.

---

## Mimari (hedef)

```
┌──────────────────┐      HTTPS/JSON      ┌─────────────────────┐      ┌──────────────┐
│  Frontend         │ ───────────────────▶ │  FastAPI (Python)    │ ───▶ │ PostgreSQL    │
│  (GitHub Pages)   │   /api/v1/...        │  Pydantic + SQLAlch. │      │ + PostGIS     │
│  index.html       │ ◀─────────────────── │  GeoPandas/NumPy*    │      │ (geom hazır)  │
└──────────────────┘                       └─────────────────────┘      └──────────────┘
        │                                                                       ▲
        └── Bugün: fetch('data.json')   →   Yarın: fetch(API_BASE+'/data')      │
                                                                  Gerçek veri ──┘
                                          (* analitik faz geldiğinde devreye girer)
```

- **Frontend** GitHub Pages'te kalır (statik, ücretsiz, hızlı).
- **Backend** ayrı bir servis (Docker ile platform-bağımsız; Render/Railway/Fly/VPS — sonra seçilir).
- **CORS** açık: frontend'in domaininden (`tarimsalkoridor.online`) API'ye erişim izinli.

---

## Veri Sözleşmesi (değişmez kontrat)

`data.json` yapısı = API'nin döndüreceği yapı:

```jsonc
{
  "meta":          { title, subtitle, note, corridor[] },
  "cropSets":      { "<key>": [ {name, yield, profit, note}, ... ] },
  "longTermCrops": { "<key>": {name, note} },
  "regions":       { "<İlçe>": { "<Mahalle>": {
      "cropSet": "<key>"  |  "crops": [ {...} ],          // biri ya da diğeri
      "longTerm": "<key>" |  "longTermCustom": {name,note},// biri ya da diğeri
      "marketGap": "<string>"
  }}}
}
```

Bu sözleşme veritabanı tablolarına şöyle düşer:

| Tablo | Alanlar | Not |
|-------|---------|-----|
| `crop_sets` | key (PK), crops (JSONB) | yeniden kullanılabilir ürün setleri |
| `long_term_crops` | key (PK), name, note | uzun vadeli yatırım ürünleri |
| `districts` | id, name, **geom (MULTIPOLYGON, nullable)** | sınır geometrisi sonra eklenir |
| `neighborhoods` | id, district_id, name, crop_set_key?, crops(JSONB)?, long_term_key?, long_term_custom(JSONB)?, market_gap, **geom (MULTIPOLYGON/POINT, nullable)** | mahalle kaydı + mekansal hazır |
| `meta` | tek satır site meta verisi | |

> **Anahtar fikir:** `geom` sütunları bugün `NULL`. Şema mekansal sorgulara (mahalle sınırı, koordinat zarfı, en yakın pazar) **hazır** ama doldurulması zorunlu değil.

---

## Fazlar

### Faz 0 — İskelet (BU TASK) ✅
- FastAPI projesi, PostGIS şeması, Pydantic şemaları, CORS, Docker Compose.
- `seed.py`: mevcut `data.json`'u veritabanına yükler.
- **`GET /api/v1/data`**: frontend'in beklediği tam JSON'u döndürür (birebir sözleşme).
- Sağlık ucu `GET /health`, otomatik dok `GET /docs`.
- **Çıktı:** `docker compose up` → çalışan API, mevcut veriyle.

### Faz 1 — Granüler API + Frontend geçişi
- `GET /api/v1/regions` (ilçe listesi), `/regions/{ilce}` (mahalleler),
  `/regions/{ilce}/{mahalle}/recommendation` (çözümlenmiş öneri: cropSet/longTerm referansları sunucuda açılır).
- Frontend'te tek satır: `const API='https://api.tarimsalkoridor.online'` ve `fetch(API+'/api/v1/data')`.
- Eski `data.json`'u fallback olarak tut (API down olursa site çalışsın).

### Faz 2 — İçerik yönetimi (admin)
- Korumalı `POST/PUT/DELETE` uçları + basit token auth.
- Artık öneriler `data.json` yerine veritabanından düzenlenir.
- (Opsiyonel) Alembic ile şema göçleri.

### Faz 3 — Gerçek veri entegrasyonu
- **Mekansal:** mahalle/ilçe sınırlarını (GeoJSON/Shapefile) `geom`'a yükle → PostGIS sorguları.
- **Toprak/İklim:** dış kaynaklardan (TARBİL, MGM, açık veri) tablolar; öneri kurallarını besle.
- **Piyasa fiyatı:** Hal fiyatları / TMO beslemesi → "yüksek verim + iyi fiyat" puanlaması.

### Faz 4 — Analitik motor (README'deki vizyon)
- GeoPandas + NumPy ile **vektörel uygunluk skoru**: toprak × iklim × fiyat × komşu ekim deseni.
- "Tragedy of the commons" çözümü: bölgesel ekim dağılımını dengeleyen öneri.
- Sonuçlar aynı API sözleşmesinden döner → frontend yine değişmez.

---

## Hemen başlama adımları (yerel)

```bash
cd agri-dss-backend
cp .env.example .env                 # değerleri düzenle
docker compose up --build            # PostGIS + API ayağa kalkar
# API:    http://localhost:8000
# Dok:    http://localhost:8000/docs
# Sözleşme testi: http://localhost:8000/api/v1/data
```

Seed otomatik çalışır (compose ilk açılışta `data/data.json`'u yükler). Manuel:

```bash
docker compose exec api python -m app.seed
```

---

## Risk / Karar notları

- **Hosting henüz seçilmedi** → her şey Docker'lı, platform-bağımsız. Render/Railway (ücretsiz katman, kolay) ya da VPS (tam kontrol) sonra seçilebilir; deploy değişmez.
- **README tutarsızlığı:** "About" FastAPI/GeoPandas/React diyordu ama repo saf statikti. Bu yol haritası o vizyonu **gerçeğe** çeviriyor — Faz 4'te GeoPandas/NumPy devreye girer.
- **Veri kalitesi:** mevcut veri "kavramsal". Gerçek veriye geçişte kaynak + metodoloji belgelenmeli (Faz 3).
- **Maliyet:** Faz 0–2 ücretsiz katmanlarda çalışır. Mekansal/analitik fazlar kaynak ister.
```
