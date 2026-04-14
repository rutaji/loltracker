# Design Doc

This document contains the technical plan for the implementation of LolTracker.

## System Architecture Overview

The following diagram depicts the layout of the project components and core technologies:

```mermaid
flowchart TD
  UI[Frontend - Jinja templates]
  API[Backend - Python / FastAPI]
  DB[(Database - PostgreSQL)]

  UI -- HTTPS/JSON --> API
  API -- SQLAlchemy --> DB
```

* **Frontend** (Jinja templates):
   * Enhanced with CSS and JavaScript
   * `MainPage`: Displays search bar users can use.
   * `SummonerPage`: View for a specific Summoner account, including calculated statistics and match history.
   * `MatchDetail`: Expanded information about  specific match.
   * `ChampionPage`: View for a specific Champion, including calculated statistics for different game modes and game versions.
* **Backend** (Python / FastAPI):
   * `DAO` (Database Access Object): Logic for the necessary CRUD-style operations with the database using SQLAlchemy.
   * `Summoner Service`: Logic for retrieving Summoner data and match history from database and calculating statistics.
   * `Champion Service`: Logic for retrieving Champion data from database and calculating statistics.
   * `Riot API Handler`: Logic for interacting with external Riot API to recieve recent match data for individual Summoners.
* **Database** (PostgreSQL)
* **Infrastructure**
   * Monitoring: Storage for monitoring data and logs.
   * Testing: pytest for unit and integration tests.
   * Deployment: Azure Cloud, GitHub Actions (CI/CD)
   * Local development: Docker

## Data Model

### Entity Relationships

![alt text](diagrams/PSI-classDiagram.svg)

The **Favorite_champions** field of **Summoner** is an array of **ChampionPlayerStats** sorted by **games_played** from highest to lowest.

### Database Migrations

Schema changes are managed with **Alembic** (the standard migration tool for SQLModel/SQLAlchemy).

| Command | Purpose |
|---|---|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back the last migration |

* Migration files live in `alembic/versions/`.
* Every migration **must** include a working `downgrade()` function.

### Database Schema

The database uses triggers to automatically update statistics in **Champion_Stats** and **Summoner** whenever a **Match_Participant** is added. Likewise the **count** field of **Matches_Analyzed** gets incremented when a new **Match** is added to the database.

![alt text](diagrams/Database.svg)

## Technologies

### Technological Dependencies

- Python 3.x
- FastAPI
- PostgreSQL
- HTTP client for communication with Riot API
- Docker

### External Dependencies

The system is dependent on the availability and functionality of the Riot Games API service. In the event where this service is unavailable, it will be impossible to update the database with new data (old data will still be available and displayed).

### API Limits

The Riot Games API limits how many requests can be sent to it within a specific period of time. As a result, the backend must implement a mechanism for limiting the flow of requests to it (rate limiting).

## API & Interface Specification

The backend application provides server-side generated HTML pages. The client (internet browser) communicates with the server via HTTP requests. User authentication is not needed for the use of any endpoints.

### Main Endpoints

| Method | Path | Description |
| ------ | --------------------- | ---------------------------- |
| `GET` | `/` | Main page of the application |
| `POST` | `/` | Searches for the given Summoner or Champion |

```json
// GET /
// 200 → Main page Jinja template
// Note: should always return 200 as it has no request body

// POST / — request body
{ "summoner_name": "ProGamer", "summoner_tagline": "1337", "champion_name": "" }
// 303 → Summoner page Jinja template if Summoner was found or Summoner not found Jinja template
// Note: the same logic applies to champion search, only one type of search is possible at a time
```

### Summoner Endpoints

| Method | Path | Description |
| ------ | --------------------- | ---------------------------- |
| `GET` | `/summoner/{name}/{tagline}` | Page with the specified Summoner's stats |
| `GET` | `/summoner/not-found` | Page displaying that the given Summoner couldn't be found |

```json
// GET /summoner/{name}/{tagline} - request body
{ "name": "ProGamer", "tagline": "1337", "offset": 0, "ajax": False}
// 200 →  Summoner page Jinja template · 303 → redirect to Summoner not found page
// Note: offset and ajax are used for match history pagination

// GET /summoner/not-found
// 200 → Summoner not found page Jinja template
```

### Champion Endpoints

| Method | Path | Description |
| ------ | --------------------- | ---------------------------- |
| `GET` | `/champion/{name}` | Page with the specified Champion's stats |
| `GET` | `/champion/not-found` | Page displaying that the given Champion couldn't be found |

```json
// GET /champion/{name} - request body
{ "name": "Ahri", "version": "14.5", "ajax": False}
// 200 →  Champion page Jinja template · 303 → redirect to Champion not found page
// Note: ajax here is used to avoid reloading the entire page when users change version

// GET /champion/not-found
// 200 → Champion not found page Jinja template
```

## Infrastructure & Deployment

>TODO: update once we start deployment

Current plan is to host the application using Azure. This will require setting up the Azure Cloud environment as well as creating a CI/CD pipeline.

High-level plan:

```mermaid
flowchart LR
    FB[Feature Branch]
    PR[Pull Request]
    MAIN[Main Branch]
    DEV[DEV environment]
    PROD[PROD environment]

    FB -- Unit Test & Code Style --> PR
    PR -- Code Review --> MAIN
    MAIN -- Build & Test --> DEV
    DEV -- Integration Tests --> PROD
```

## Reliability & Observability

This project uses OpenTelemetry-first observability for all backend runtime telemetry.

### Local observability stack

The local development environment includes a pre-wired monitoring stack in Docker:

| Service | Purpose | Port(s) |
|---|---|---|
| `otel-collector` | Central OTLP receiver and fan-out pipeline | `4317`, `8889` |
| `jaeger` | Distributed tracing UI | `16686` |
| `prometheus` | Time-series metrics storage and query engine | `9090` |
| `grafana` | Dashboards and alert visualization | `3000` |

When running the stack, application traffic is observed through this flow:

1. FastAPI emits traces and metrics through OTLP.
2. OpenTelemetry Collector receives telemetry and routes:
    * traces to Jaeger
    * metrics to Prometheus exporter endpoint
3. Prometheus scrapes collector metrics and stores them.
4. Grafana queries Prometheus and renders dashboards.

### Instrumentation design

The backend instrumentation strategy combines automatic and manual telemetry:

* **Auto-instrumentation**
   * FastAPI request spans (`opentelemetry-instrumentation-fastapi`)
   * SQLAlchemy operation spans (`opentelemetry-instrumentation-sqlalchemy`)
   * HTTP client spans for outbound Riot API requests (`opentelemetry-instrumentation-httpx`)
* **Manual service-level spans**
   * Summoner and champion service methods add domain context (cache hit/miss,
      pagination, route-specific operation outcomes)
* **Custom metrics**
   * `psi_http_server_requests_total` (counter)
   * `psi_http_server_request_duration_seconds` (histogram)

Resource attributes are configured to identify environment and service instance:

* `service.name`
* `service.version`
* `deployment.environment`

Telemetry sampling is configurable via `PSI_OTEL_TRACES_SAMPLER_ARG`.

### SLI / SLO targets

The monitoring design tracks reliability with explicit indicators and targets:

| SLI | Target SLO | Window |
|---|---|---|
| API availability | >= 99.0% successful requests | 30 days |
| P95 request latency (safe page endpoints) | < 400 ms | 30 days |
| 5xx error ratio | < 1.0% | 30 days |

These targets are development-stage defaults and can be tightened for production.

### Dashboard and alerting model

Grafana dashboards are provisioned from repository files and should cover:

* Request throughput (req/s)
* Error throughput (5xx req/s)
* P95/P99 request latency
* Route-level request distribution

Alerting should be based on rate and sustained threshold conditions rather than
single-point spikes. Recommended initial alerts:

* Elevated 5xx rate for 5 minutes
* P95 latency above threshold for 10 minutes
* Collector or Prometheus target marked down

### Verification and load testing

Basic telemetry verification:

1. Start stack with `docker-compose up --build`.
2. Generate traffic from browser or load script.
3. Verify traces in Jaeger (`psi-api` service).
4. Verify metrics in Prometheus (`psi_http_server_requests_total`,
    `psi_http_server_request_duration_seconds`).
5. Verify dashboard panels in Grafana.

Load testing is provided by:

```bash
source .venv/Scripts/activate
python -m scripts.load_test --base-url http://localhost:8000 --duration 120 --concurrency 40
```

The default request mix is intentionally safe (home and champion endpoints) so
Riot API-heavy endpoints are not stressed unless explicitly configured.

### Operational notes

* Keep metric labels low-cardinality (use route templates, not raw URLs).
* Do not emit secrets or Riot API tokens in span attributes or logs.
* Use Grafana credentials from `.env` (`GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`).
* In production, use persistent volumes and non-default credentials for all monitoring services.

## Testing Strategy

### Unit Tests

**Backend** - pytest with `pytest-cov`:

* Tests cover the service layer and API route handlers; the persistence layer is replaced with in-memory fakes.
* Coverage target: **≥ 80 %** line coverage, enforced in CI with `--cov-fail-under=80`.
* Run locally to generate an html with results, alternatively use `--cov-report=term-missing` to recieve results in terminal:
```bash
source .venv/Scripts/activate
PSI_OTEL_ENABLED=false pytest --cov=app --cov-report=html
#This disables telemetry while testing, removing OpenTelemetry's attempts at exporting information into an inactive docker container.
```

### Integration Tests

Run all tests:

  pytest -ra

Run only integration tests:

  pytest -m integration -ra

Run only non-integration tests (fast unit/service/endpoint checks):

  pytest -m "not integration" -ra

Integration tests cover endpoint -> service -> DAO -> database flow while stubbing Riot API calls for deterministic runs.

### CI/CD Quality Gates

| Stage | Checks |
|---|---|
| PR (every push) | `pytest` with coverage gate (currently run locally) |
| Merge to `develop` | All PR checks + code review |
| Deploy to `main` | _(Azure — milestone 3)_ |