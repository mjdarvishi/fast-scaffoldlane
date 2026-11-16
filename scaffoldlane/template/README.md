# __PROJECT_NAME__

Generated FastAPI project with a reusable core and a default auth feature in `app/features`.

```bash
uv sync
uv run project config init
uv run project generate domain example
uv run project run
uv run project docker up -d
uv run project db migrate
uv run project deploy normal
```

The health endpoint is `/v1/health`. PostgreSQL is available with `docker compose -f deployment/docker-compose.yml up -d`.
The standard deployment serves the app on port 8000. Install the optional blue-green addon to use `project deploy blue-green` and `project rollback blue-green` with Caddy on port 80. The `lint`, `format`, and `test` commands require Ruff and pytest in your development environment.
Register generated feature routers in `app/api/v1/__init__.py`.
