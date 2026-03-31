
# 🚀 PSI 2026 - LolTracker

Repository with supporting code for PSI (Pokročilé Softwarové Inženýrství) course at Technická Univerzita of Liberec (_TUL_).

The repository hosts a the **LolTracker** project, a site allowing users to view detailed statistics about player accounts (called Summoners) and playable characters (called Champions) for the game League of Legends.

## User scenarios

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
* [`specification/SPECIFICATION.md`](specification/SPECIFICATION.md) provides product-oriented description: business objectives and motivation, planned user scenarios, functional requirements and scope.
* [`specification/DESIGN.md`](specification/DESIGN.md) (in-progress) contains engineering-oriented documentation: technical architecture, UML diagrams, API contracts and DB schema.

## 💻 Local development

The AI-made prototype of the app can be run locally, see the [prototype/README.md](prototype/README.md) for further instructions.

The application itself can be run locally on port 8000 by first creating a .env file (see [.env.example](.env.example)) and then using:
        docker-compose up --build
        alembic upgrade head

### SQL database

You can connect to database using: postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}

To generate new alembic version: alembic revision --autogenerate -m "commit-name"

To upgrade to newest alembic version: alembic upgrade head

To add test data into database (not functional yet): docker-compose exec api python -m  scripts.seed_data

## 🎯 Project milestones

* **Milestone 1: prototype** (3.3.2026): Specification, prototype & high-level design.
* **Milestone 2: mvp** (7.4.2026): MVP is ready, CI/CD is working (dev environment).
* **Product launch** (5.5.2026): Final demo, code/test/documentation is ready, deployed to Azure (dev & prod) with NFRs met (monitoring).

## 👥 Team

* **Ondřej Braunšveig** (@OndrejBraunsveig) – Search functionality
* **Martin Čížek** (@cizek-maritn) – FastAPI endpoints, endpoint services, documentation
* **Jiří Růta** (@rutaji) – PostgreSQL database

## 📊 NFR Status

TODO: Complete the following items to fulfill the NFRs of PSI:
* [ ] Production: Link to the app in Production and Dev environments
* [ ] Monitoring: Link to Azure App Insights (monitoring dashboard)
* [ ] Tests: Link to code coverage and latest unit & integration test results on `main` branch
* [ ] CI/CD: Link to GitHub actions forming fully autonomous delivery of (working) code from `main` through `dev` to `prod` environments in a selected cloud (Azure is recommended).
* [ ] SLO: Aiming at 99% availability - provide a link to SLI dashboard
