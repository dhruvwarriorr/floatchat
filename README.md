# FloatChat-Lite

A frontend-only SIH demonstration for exploring illustrative Indian Ocean temperature, salinity, and trend data through natural-language questions.

The scientific values are bundled locally for the interface walkthrough. The app has no backend, database, authentication, API keys, external map tiles, or external data requests.

## Requirements

- Node.js 22.13 or newer

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Quality checks

```bash
npm run build
npm run lint
npm test
```

## Supported questions

- Show temperature profile near Mumbai in July 2024
- Plot SST time series at 19N, 72.8E from 2015–2024 and tell me if it is unusual
- Show average salinity in the Bay of Bengal in 2023
- Is the Arabian Sea warming over time?

Any unsupported question returns a friendly prompt to use one of the available examples.

## Map and data boundaries

The regional map uses bundled, simplified GeoJSON coastline geometry rendered directly as SVG. It makes no runtime network requests and is intended for geographic context, not navigation or GIS analysis.
