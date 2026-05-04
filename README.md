
# 🚀 PSI 2026 - LolTracker

[![Coverage](https://codecov.io/gh/rutaji/loltracker/branch/main/graph/badge.svg)](https://codecov.io/gh/rutaji/loltracker)

Repository with supporting code for PSI (Pokročilé Softwarové Inženýrství) course at Technická Univerzita of Liberec (_TUL_).

The repository hosts a the **LolTracker** project, a site allowing users to view detailed statistics about player accounts (called Summoners) and playable characters (called Champions) for the game League of Legends.

## 🧑‍💻 User scenarios


**LolTracker** allows the following:
* Allows users to search for Summoners and Champions through a search bar.
* Lists calculated statistics for individual Summoners including a global win rate ratio and KDA (_Kills, Deaths and Assists_).
* Shows the match history of individual Summoners including basic information for each match.
    * Provides a detailed view of individual matches containing more thorough information such as team composition.
* Displays globally calculated statistics for individual Champions throughout different versions.

## 🛠️ Tech Stack

The following diagram depicts the layout of the project components and core technologies:

```mermaid
flowchart TD
  UI[Frontend - Jinja templates]
  API[Backend - Python / FastAPI]
  DB[(Database - PostgreSQL)]

  UI -- HTTPS/JSON --> API
  API -- SQLAlchemy --> DB
```

## 📖 Documentation

* This `README.md` contains quick introduction to the product, onboarding guide, local setup of the project and a rough user guide.
* [`specification/specification.md`](specification/specification.md) provides product-oriented description: business objectives and motivation, planned user scenarios, functional requirements and scope.
* [`specification/design.md`](specification/design.md) contains engineering-oriented documentation: technical architecture, UML diagrams, API contracts and DB schema.
* [`specification/SQL-specification.md`](specification/SQL-specification.md) gives an in-depth overview of the database used within this project.

## 💻 Local development

The AI-made prototype of the app can be run locally, see the [prototype/README.md](prototype/README.md) for further instructions.

The application itself can be run locally on port 8000 by first creating a .env file (see [.env.example](.env.example)) and then using:

        docker-compose up --build

## 🔭 Observability stack (OpenTelemetry + Prometheus + Jaeger + Grafana)

The backend now exports traces and metrics via OpenTelemetry to an in-stack OpenTelemetry Collector.

When running the Docker stack, the following UIs are available:
* FastAPI: http://localhost:8000
* Jaeger (traces): http://localhost:16686
* Prometheus (metrics): http://localhost:9090
* Grafana (dashboards): http://localhost:3000

Default credentials for Grafana are loaded from `.env`:
* `GRAFANA_ADMIN_USER`
* `GRAFANA_ADMIN_PASSWORD`

For more detailed information, see [`specification/design.md#reliability--observability`](specification/design.md#reliability--observability)

### 💾 SQL database

You can connect to database using: postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}

To generate new alembic version: alembic revision --autogenerate -m "commit-name"

To upgrade to newest alembic version: alembic upgrade head

To add test data into database: docker-compose exec api python -m  scripts.seed_data

For more detailed information, see [`SQL-specification.md`](SQL-specification.md)


## 🎯 Project milestones

* **Milestone 1: prototype** (3.3.2026): Specification, prototype & high-level design.
* **Milestone 2: mvp** (7.4.2026): MVP is ready, CI/CD is working (dev environment).
* **Product launch** (5.5.2026): Final demo, code/test/documentation is ready, deployed to Azure (dev & prod) with NFRs met (monitoring).

## 👥 Team

* **Ondřej Braunšveig** (@OndrejBraunsveig) – Search functionality, Riot API calling, frontend design, Summoner page
* **Martin Čížek** (@cizek-maritn) – Champion page, Riot data ingestor, documentation, observability stack
* **Jiří Růta** (@rutaji) – PostgreSQL database, DAO (Database Access Object), logging, deployment

## 📊 NFR Status

The NFRs of this project:
* ✅ Production: [Link](https://fastapi-app.calmrock-7cb3a497.polandcentral.azurecontainerapps.io/) to the app in Production environment
* ✅ Monitoring: [Link](https://portal.azure.com/#@tulib.onmicrosoft.com/resource/subscriptions/3e7579de-1963-4142-832d-f1fb66426b85/resourceGroups/loltrackerResourceGroup/providers/Microsoft.Insights/components/loltracker-insights/overview) to Azure App Insights (monitoring dashboard)
* ✅ Tests: Code coverage badge and latest unit & integration test results on `develop` branch
* ✅ CI/CD: [Link](https://github.com/rutaji/loltracker/actions) to GitHub actions forming fully autonomous testing of code from `feat` branches to `develop`.
