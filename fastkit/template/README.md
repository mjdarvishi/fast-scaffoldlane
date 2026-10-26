# __PROJECT_NAME__

Generated FastAPI project with a reusable core and an empty `app/features` package.

```bash
uv sync
uv run project generate domain example
uv run uvicorn main:app --reload
```

The health endpoint is `/v1/health`. PostgreSQL is available with `docker compose up -d`.
Register generated feature routers in `app/api/v1/__init__.py`.
