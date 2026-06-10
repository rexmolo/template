# SaaS Template

Reusable, API-first SaaS template for web and future native mobile clients.

## Local Bootstrap

Start the local infrastructure services:

```sh
docker compose up -d postgres redis
```

Run the API placeholder tests:

```sh
cd services/api
uv run pytest
```

## Workspace Layout

- `services/api` - FastAPI backend.
- `apps/app` - product web app.
- `apps/site` - public brand/content site.
- `packages/contract` - generated API contract artifacts.
- `packages/brand` - shared brand tokens.
- `scripts` - project automation.
