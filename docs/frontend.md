# Frontend Architecture

This repository includes a very lightweight Next.js client used mainly for
proof-of-concept and developer UI testing.  The current implementation
consists of a search page, a login screen, and a simple property detail view
with ARV range and report generation.  Advanced features such as maps, widgets
and caching are planned for later enhancement.

## 7.1 Tech Stack

- **Framework:** Next.js (App Router)
- **UI:** React, Tailwind CSS, Recharts
- **Map:** Leaflet.js with `leaflet.markercluster`, `leaflet-draw`,
  `leaflet.heat`
- **Data fetching:** React Query

## 7.2 Page & Component Structure

### 7.2.1 Pages

- `/` – search page with map and listing grid
- `/properties/[id]` – property detail (SSR)
- `/neighborhoods/[slug]` – neighborhood overview (SSG with ISR every 6 h)
- `/reports/[id]` – download generated PDF

### 7.2.2 Map Module

- Base tiles from OpenStreetMap (`tile.openstreetmap.org`)
- Marker clustering for performance with 1k+ markers
- Color-coded markers by ARV confidence (green/amber/red)
- Popup cards with address, type, sqft, ARV range, and detail link
- Draw tool to select custom polygons for area searches
- Neighborhood boundaries overlay via GeoJSON
- Optional heatmap layer showing price density

### 7.2.3 ARV Widget

- Interactive horizontal range bar using Recharts
- Displays P10 (low), P50 (mid), P90 (high) values
- Confidence band color: green (>0.8), amber (0.6–0.8), red (<0.6 or thin)
- Toggle to display renovation scenario overlays (e.g., "after kitchen
  remodel: +$85K–$140K")

## 7.3 Performance

- Static generation for neighborhood pages, regenerated every 6 h (ISR).
- SSR for property details for SEO & freshness.
- React Query caches property API responses for 5 minutes on client.
- Next.js image optimization component for property photos.
- Nginx serves static JS/CSS with gzip compression and 1-year cache headers.
- Web Vitals targets: LCP < 2.5s, FID < 100 ms, CLS < 0.1.
