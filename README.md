# Setu Sentinel

A live, public health scorecard for Indian government portals — uptime, accessibility, and translation quality, refreshed automatically, on entirely free infrastructure.

> **Note on Languages:** During the development phase, Setu Sentinel will focus exclusively on **English and Hindi** translation quality. Support for additional regional languages may be added in future production releases.

## Project Structure

- `checks/`: Modules for checking uptime, accessibility, and translation quality.
- `scoring/`: Logic for generating a composite health score for each portal.
- `data/`: The portal list (`portals.json`) and snapshot history (`history/`).
- `dashboard/`: A simple dashboard to view the health of the portals.

*Note: This is an independent civic-tech project and is not affiliated with the Government of India.*
