<div align="center">

# AGRI-DSS

### A Decision Support System for Agricultural Planning in the Western Antalya Corridor

[![Status](https://img.shields.io/badge/status-prototype-0C8A3C.svg)](https://tarimsalkoridor.online)
[![Architecture](https://img.shields.io/badge/architecture-static_client--side-13140F.svg)](#architecture)
[![License](https://img.shields.io/badge/license-Apache--2.0-13140F.svg)](./LICENSE)

**Live:** [tarimsalkoridor.online](https://tarimsalkoridor.online) · **Region:** Demre · Finike · Kaş · Kemer · Kumluca · **Envelope:** 36.18°N–37.12°N / 29.30°E–30.85°E

</div>

---

## What it is

**Agri-DSS turns local agronomic and economic knowledge into a decision a farmer can act on.**
Pick a district and a neighborhood, and the system returns a concrete, defensible plan: the
seasonal crops most likely to deliver yield *and* profit, a long-term orchard/tree investment
suited to the land, and an emerging market opportunity to watch — all printable on a single A4
sheet for a village board or cooperative.

It is built for the **Western Antalya agricultural corridor** (Demre, Finike, Kaş, Kemer,
Kumluca): five districts, **147 neighborhoods**, each with a curated recommendation profile.

---

## The problem it solves

### Tragedy of the Commons in the field

Farmers acting in isolation tend to plant whatever looked profitable *last* season — everyone
plants tomatoes at once. The predictable result at harvest is **oversupply, a price collapse
below cost, wasted produce, and a losing year** for the very growers who worked hardest.

### Data-driven coordination

Agri-DSS is designed to go beyond "what's the weather?" and "when do I fertilize?". Its goal is
to recommend, for each neighborhood, the crop that **optimizes profitability** — weighing not
only soil and climate but also expected market prices and (in a future phase) what other
growers in the region are already planting. The question it answers:

> *"If I plant this, will I get both high yield and a strong harvest-time price — and therefore
> maximum profit?"*

---

## What it does

- **Dynamic region selection** — filter by District → Neighborhood across a clean, guided flow.
- **Seasonal recommendations** — the best soil-based crops for the selected area, each rated for
  **estimated yield**, **estimated profitability**, and an **agronomic/economic rationale**.
- **Long-term investment advice** — a tree/orchard crop matched to the land and climate
  (avocado, olive, pomegranate, almond, geographically-protected Finike orange, and more).
- **Conceptual market analysis** — an emerging demand / supply-gap opportunity for the area.
- **Printable report** — a typographic A4 layout ready for village boards and cooperatives.

---

## Architecture

Agri-DSS is a **fully client-side static site** — no backend, no build step. This makes it
trivially hostable (GitHub Pages), instantly auditable, and impossible to break with a server
outage.

```
index.html   →  Interface + all DSS logic (custom Swiss-style UI, vanilla JS)
data.json    →  Data layer — content is decoupled from code
CNAME        →  Custom domain (tarimsalkoridor.online)
LICENSE      →  Apache-2.0
```

### Design

The interface follows the **Swiss / International Typographic Style**: a strict modular grid,
strong typographic hierarchy (Archivo + Space Mono), generous negative space, and a single
decisive accent — agricultural green on warm paper. The experience is interactive (guided
stepper, corridor diagram, staggered result reveals, live counters) yet collapses to a clean,
ink-on-white A4 document when printed.

### Data model (`data.json`)

Data is stored in a compact, DRY structure so the catalogue can be edited without touching code:

| Key | Purpose |
|---|---|
| `cropSets` | Reusable seasonal crop sets (e.g. `seraDomatesBiberSalatalik`) |
| `longTermCrops` | Dictionary of long-term investment crops (e.g. `avokado`, `zeytin`) |
| `regions` | District → Neighborhood → record |

Each neighborhood record carries either a `cropSet` reference **or** an inline `crops` list;
either a `longTerm` reference **or** an inline `longTermCustom`; plus a `marketGap` string.
`index.html` fetches `data.json` on load and resolves these references at runtime.

> **To update recommendations, edit `data.json` only — no code changes required.**

---

## Run locally

Because `data.json` is loaded via `fetch`, open the site through a web server rather than
double-clicking the file:

```bash
# from the repo root:
python3 -m http.server 8000
# then open http://localhost:8000
```

---

## Deploy (GitHub Pages)

1. Push to the `main` branch.
2. **Settings → Pages → Source: Deploy from a branch → `main` / `root`.**
3. The root `CNAME` binds `tarimsalkoridor.online`; point your DNS records at GitHub Pages.

There is no build pipeline — `index.html` and `data.json` are published as-is.

---

## Data note

The current dataset is **conceptual**, derived from regional reports (economy, environment,
land use, climate). It demonstrates the system's logic and interface. In production, the same
`data.json` contract can be backed by real soil, climate, and market data sources — without any
change to the application code.

---

## License

Released under the **Apache-2.0** license. See [`LICENSE`](./LICENSE) for details.
