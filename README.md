# Provenance

An interactive globe of live environmental and energy data, coloured by **how each
number was produced** rather than by what it says.

Brightness encodes verifiability. Almost nothing on the globe is bright.

**Live:** _(add deployment URL)_

---

## The argument

Most environmental data is not measured where it is displayed. It is interpolated
from satellite radiance and reanalysis models, then rendered as a confident number
at a specific coordinate. Carbon markets, ESG disclosures and the new AI energy
reporting regimes all sit on top of that layer.

The counter is a live figure: what fraction of the readings currently on screen can
be verified without trusting whoever published them.

Walk the provenance dial from *Anything* down to *Cryptographically attested* and
watch the globe empty. That collapse is the whole point.

## Provenance tiers

| Tier | Meaning |
|---|---|
| **Modeled** | Interpolated from satellite and reanalysis. No instrument at this location. |
| **Inferred** | Emissions estimated from satellite imagery and ML. Independent of the operator, but nobody metered it. |
| **Instrument** | A real instrument, published by an agency. You trust the agency, not the number. |
| **Self-reported** | Operator disclosure. Annual, aggregated, unaudited, no third party. |
| **Attested** | Signed in a secure element at the moment of measurement. Verifiable without trusting the reporter. |
| **Orbital sensor** | The instrument itself, in orbit. Everything it produces is inferred radiance. |

## Data sources

All feeds are public and unauthenticated. There are no API keys and no metered
tiles, so traffic costs nothing at any volume.

| Layer | Source | Notes |
|---|---|---|
| PM2.5, 72 cities | [Open-Meteo](https://open-meteo.com) CAMS | hourly model output |
| 1,200 emitting facilities | [Climate TRACE](https://climatetrace.org) v7 API | embedded snapshot, see below |
| Seismic, M2.5+ | [USGS ANSS](https://earthquake.usgs.gov) | past 7 days |
| 1,557 PM2.5 monitors | [EPA AQS](https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/AQSmonitor_sites/MapServer) | United States only, embedded snapshot |
| Hyperscale campuses | operator sustainability reports | static list, annual disclosure |
| Orbital sensors | [CelesTrak](https://celestrak.org) elements, propagated with SGP4 | embedded snapshot, see below |
| Full-disk imagery | [NOAA STAR](https://cdn.star.nesdis.noaa.gov) GOES-19 / GOES-18 | 10 minute refresh, geocolor and band 13 |
| Coastlines | [world-atlas](https://github.com/topojson/world-atlas) 110m | TopoJSON decoded inline |

Built with three.js and satellite.js. One file, no build step, no dependencies to install.

## The sensor feed panel

The panel shows whatever the selected object actually produces, and nothing more:

| Selection | Feed |
|---|---|
| GOES-19 / GOES-18 | real NOAA full-disk frame, geocolor or band 13 thermal |
| any other satellite | rendered view from its true orbital position, labelled simulated |
| modelled PM2.5 point | 96 hours of model output, continuous by construction |
| EPA monitor | its declared 30-day sampling cadence, gaps included |
| Climate TRACE facility | **no feed** |
| operator disclosure | **no feed** |

The empty states are not missing features. A facility whose emissions were
inferred from imagery has no instrument to read, and the panel says so.

## Honesty notes

This is a demo about data provenance, so it does not fake its own data.

- The **Satellite view** panel is a *render of the 3D model* from a satellite's real
  current position, not photography. Every frame is labelled `SIMULATED`. Real NOAA
  frames are labelled `REAL` with a fetch timestamp.
- The **attested nodes** layer is illustrative and labelled as such. It represents
  what attestation would look like, not a live deployment. The default attested
  count is zero, and that zero is the honest reading.
- Satellite **altitude is log-compressed** on the globe so LEO and GEO are visible
  together. The readout shows true kilometres. The satellite-view camera uses true
  altitude so the Earth subtends its correct angular size.

## The monitor layer

The EPA AQS layer is the counterpart to the modelled PM2.5 layer, and the
comparison is the argument in miniature. The model produces a value for every
coordinate on Earth. The United States regulatory network is 1,557 devices, each
identified by make and model and sited to a stated accuracy in metres.

About a quarter of them do not sample daily: 13% run every third day, 10% every
sixth, 3% every twelfth. On the days a monitor does not run, the number for that
place comes from a model. Even the instrument tier is mostly interpolation.

This layer is United States only. Other countries operate their own networks;
their absence here is a gap in this dataset, not in the world.

Refresh with `python3 tools/refresh-aqs.py`, which rewrites the embedded block in `index.html`.

## Refreshing the Climate TRACE snapshot

Climate TRACE asks API users to keep volume low and states that the v7 API is
beta and not guaranteed for production. The facility data is therefore pulled
once and shipped as a static file rather than called from every visitor's
browser. Refresh it when they publish a new release:

```bash
python3 tools/refresh-climate-trace.py
```

The snapshot is embedded directly in `index.html`. Keeping the page a single
self-contained file matters more than repo tidiness: it has to work from disk,
from an email attachment, and inside a sandboxed iframe, none of which can
fetch a sibling file.

Climate TRACE data are free and publicly available. Cite them per
[their guidance](https://climatetrace.org/data).

## Refreshing orbital elements

TLEs lose accuracy over weeks. They are embedded rather than fetched because
CelesTrak sends no CORS header and the public mirrors rate-limit at roughly five
requests. Refresh monthly:

```bash
python3 tools/refresh-tle.py
```

The script rewrites the `const TLE=[...]` block in `index.html` and refuses to
write if fewer than ten satellites resolve.

## Running locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Opening `index.html` directly with `file://` works too. Everything except the
live feeds is embedded, so the page is fully self-contained.

## Licence

MIT
