# Agri-DSS Backend (Faz 0)

Batı Antalya Tarımsal Karar Destek Sistemi için **sözleşme öncelikli** FastAPI + PostGIS backend'i.
Mevcut `data.json`'u veritabanına yükler ve frontend'in beklediği JSON'u **birebir** servis eder.

> Tam strateji ve fazlar için bkz. [`ROADMAP.md`](./ROADMAP.md).

## Hızlı başlangıç (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- API: <http://localhost:8000>
- Otomatik dokümantasyon (Swagger): <http://localhost:8000/docs>
- **Sözleşme testi:** <http://localhost:8000/api/v1/data>  ← frontend'in beklediği tam JSON
- Sağlık: <http://localhost:8000/health>

Seed (mevcut `data.json` → DB) ilk açılışta otomatik çalışır. Manuel:

```bash
docker compose exec api python -m app.seed
```

## Uç noktalar

| Method | Yol | Açıklama |
|--------|-----|----------|
| GET | `/api/v1/data` | data.json'un birebir aynısı (frontend bunu tüketir) |
| GET | `/api/v1/regions` | İlçe listesi |
| GET | `/api/v1/regions/{ilce}` | İlçedeki mahalleler |
| GET | `/api/v1/regions/{ilce}/{mahalle}/recommendation` | Çözümlenmiş öneri (cropSet/longTerm açılmış) |
| GET | `/health` | Sağlık kontrolü |

## Frontend geçişi (tek satır)

`index.html` içinde veri çekme kısmını değiştir — başka hiçbir şey değişmez:

```js
// ESKİ:
// const res = await fetch('data.json');

// YENİ (API down olursa data.json'a düş):
const API = 'https://api.tarimsalkoridor.online'; // veya http://localhost:8000
let data;
try {
  const res = await fetch(`${API}/api/v1/data`);
  if (!res.ok) throw new Error('API hata');
  data = await res.json();
} catch (e) {
  data = await (await fetch('data.json')).json(); // fallback
}
```

## Mimari notu — mekansal hazırlık

`districts.geom` ve `neighborhoods.geom` sütunları **bugünden tanımlı ama boş (NULL)**.
Gerçek sınır/koordinat verisi geldiğinde aynı şemaya doldurulur; PostGIS sorguları
(mahalle sınırı, koordinat zarfı 36.18–37.12°N / 29.30–30.85°E, en yakın pazar) o an açılır.
Uygulama kodu değişmez.

## Yerel geliştirme (Docker'sız)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Çalışan bir PostGIS gerekir; DATABASE_URL'i ona göre ayarla
export DATABASE_URL='postgresql+psycopg2://agri:agri@localhost:5432/agridss'
python -m app.seed
uvicorn app.main:app --reload
```

## Sonraki adım

`ROADMAP.md` → Faz 1: granüler API'ye geçiş + frontend entegrasyonu.
