# Copilot Instructions

This repository contains a Python backend built with FastAPI and a test suite based on `pytest`.

## Core Expectations

- Write clean, readable, and maintainable code.
- Prefer simple, explicit solutions over clever or overly abstract ones.
- Keep functions and modules focused on a single responsibility.
- Try to keep components and units of logic small and focused.
- Use clear naming and consistent structure that matches the existing codebase.
- Every function should include Python type hints.
- Add comments only when they explain why something is done, not what the code is doing.

## Dead Code

- Do not leave dead code in the repository.
- Remove unused imports, commented-out logic, obsolete helpers, and unreachable branches.
- When replacing an implementation, clean up the old code instead of keeping both versions around.

## Backend Conventions

- Treat FastAPI as the backend framework for this project.
- Follow FastAPI patterns for routing, request handling, and response behavior.
- Keep endpoint logic thin when possible and place reusable business logic into services or other appropriate modules.
- Preserve compatibility with the current application structure under `app/`.
- Use Pydantic models for all request and response bodies.
- Write API endpoints so FastAPI can generate documentation automatically.
- Prefer `async def` for routes and database operations where appropriate.
- Use FastAPI exceptions whenever they are the right fit for the error handling case.

## Testing

- Use `pytest` for all backend tests.
- Add or update tests whenever backend behavior changes.
- Prefer clear, isolated tests that verify observable behavior.
- Follow the existing test style in the `tests/` directory and use FastAPI's `TestClient` where appropriate.
- Mock external dependencies in unit tests so tests stay fast and effective.
- Aim for at least 80% test coverage.

## Code Quality Checklist

Before suggesting or generating code, make sure that:

- The code is clean and easy to understand.
- No dead code is introduced or left behind.
- Backend changes align with FastAPI conventions.
- Functions include Python type hints.
- Request and response bodies use Pydantic models.
- Endpoints support automatic FastAPI documentation generation.
- Comments explain why, not what.
- Tests are written or updated using `pytest`.
- Unit tests mock external dependencies when needed.
