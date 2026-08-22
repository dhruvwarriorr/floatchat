# FloatChat-Lite

A React/TypeScript client for the FloatChat-Lite FastAPI runtime. It renders real query responses from the installed Arabian Sea ARGO subset, including interactive charts, a Leaflet map, QC/evidence disclosures, and source-row provenance.

The browser calls only `POST /chat`; it never reads scientific artifacts or provider keys. CARTO/OpenStreetMap tiles provide geographic context, while all ARGO selection and computation stays in FastAPI.

## Requirements

- Node.js 22.13 or newer

## Run locally

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`.

## Quality checks

```bash
npm run build
npm run lint
npm test
```

## Example questions for the installed subset

- Show temperature profile at 10N 70E within 150 km in July 2024
- Compare temperature and salinity at 10N 70E from 2022–2024 over time
- Show average salinity in the Arabian Sea in 2023
- Is shallow-water temperature near 10N 70E unusual from 2015–2024?

The parser accepts arbitrary free-form Indian Ocean temperature/salinity questions. The installed artifacts cover only the Arabian Sea, so other locations return a friendly `no_data` response.

## Map and data boundaries

The interactive Leaflet map uses CARTO dark tiles, an exact query marker, a radius or named-region overlay, pan/zoom controls, and attribution. It is contextual and not for navigation.
