# FastKit

FastKit is an installable CLI for starting FastAPI projects with a reusable application backbone. It copies a template containing configuration, dependency injection, PostgreSQL data access, authentication helpers, logging, a versioned API, and feature generators. New projects have an empty `app/features` package. The source application's company, vehicle, Telegram, and other business features are not included.

FastKit currently creates projects and generates feature code.

Optional integrations can be added to generated projects with `fastkit add`.

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/) to follow these commands. You can also install the CLI with `pipx`.
- Git for the default repository initialization. Use `--no-git` if Git is unavailable.
- Docker with Compose if you want to run the provided PostgreSQL service.

## Install the CLI

After publishing to PyPI:

```powershell
uv tool install fastkit-project-generator
fastkit --help
```

Alternatively, install in a Python environment with `python -m pip install fastkit-project-generator`. The `fastkit` executable is then available in that environment's scripts directory.

For local development, from this repository's `fastkit` directory:

```powershell
uv tool install .
fastkit --help
```

After changing the local CLI or template, run `uv tool install --reinstall .`. If PowerShell reports that `fastkit` is not recognized, add uv's tool directory to the current terminal's `PATH`:

```powershell
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
fastkit --help
```

Run `uv tool update-shell` and open a new terminal to make the tool directory available in future sessions.

The PyPI distribution name is `fastkit-project-generator`; the CLI command remains `fastkit`. The `fastkit` and `fastkit-cli` distribution names belong to other projects.

## Publish a release

From this repository's `fastkit` directory, update the version in `pyproject.toml`, then build and inspect the distributions before uploading:

```powershell
uv build --no-sources
uv publish
```

`uv publish` needs a PyPI token or configured trusted publishing. Each published version is immutable; increment the version for later releases.

## Create a project

Run this from the directory in which you want the new project folder:

```powershell
fastkit new inventory_api
cd inventory_api
```

The name must start with a lowercase letter and may contain lowercase letters, digits, and underscores. FastKit will not overwrite an existing folder.

`new` copies the bundled template, replaces the project-name placeholders, and initializes a Git repository. It does not create a Git commit or install the generated project's dependencies.

```powershell
fastkit new inventory_api --destination C:\projects
fastkit new inventory_api --no-git
fastkit new --help
```

`--destination` is the parent directory, so the first example creates `C:\projects\inventory_api`.

## Run the generated application

In the generated project:

```powershell
Copy-Item .env.example .env
docker compose up -d
uv sync
uv run uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/v1/health> for the health endpoint or <http://127.0.0.1:8000/docs> for FastAPI's default API documentation. PostgreSQL is exposed on local port `5432`; change the Compose mapping if that port is already in use.

The example `.env` contains development credentials and a placeholder token secret. Replace them before using the project outside local development. The health route can run without an active PostgreSQL connection, but database features need the Compose service or another configured PostgreSQL instance.

## Add Redis

From a generated project directory, run:

```powershell
fastkit add redis
uv sync
docker compose up -d redis
```

Or use `fastkit add redis --project .\inventory_api` from another directory. The command adds `app/core/redis/connection.py` and `kv_service.py`, Redis settings, a Compose service, the `redis` Python dependency, and startup/shutdown wiring. It refuses to overwrite an existing Redis integration. Configure a remote Redis instance with `REDIS__HOST`, `REDIS__PORT`, `REDIS__DB`, and `REDIS__PASSWORD` in `.env`; the bundled Compose service is intended for local development without a password.

`MainRedisConnection` connects in a background retry loop, so application startup does not wait for Redis. Check `is_connected` if a feature needs to report readiness. Inject `RedisKVService` for common key-value operations, or `MainRedisConnection` for direct Redis commands. The service manager owns connection shutdown.

Future optional integrations belong under `fastkit/addons/<name>/`, with their own installer and copied files. The `fastkit add` command group keeps these separate from feature/domain generation.

## Add tracing

From a generated project directory, run:

```powershell
fastkit add tracing
uv sync
```

This adds OpenTelemetry configuration, tracing bootstrap, repository spans, and trace-aware structured logging. Tracing starts disabled; set `TRACING__ENABLED=true` and `TRACING__OTLP_TRACES_ENDPOINT` in `.env` to export traces. You can also set `TRACING__SERVICE_NAME`. If Redis is installed, its key-value service gains Redis spans. Redis and tracing can be added in either order. New projects have no OpenTelemetry dependency until tracing is added.

## Generate features

From the generated project directory:

```powershell
fastkit generate domain product
fastkit generate model product item
fastkit generate listener product product_created
```

From another directory, point the CLI at the project:

```powershell
fastkit generate --project .\inventory_api domain product
```

`generate domain` creates data, domain, and presentation folders with starter code. `generate model` adds an entity and database DTO to an existing domain. `generate listener` adds a listener to an existing domain; use `--event module.path:EventClass` to select its event class. The generators accept `--force` to overwrite generated files. Inspect existing code before using that option.

FastKit delegates generation to the generated project's `dev_cli` package, so each project's generator matches the template version it was created with. Run `fastkit generate --project PATH --help` or `fastkit generate --project PATH domain --help` for command options.

After creating a domain, register its router in `app/api/v1/__init__.py` if it should expose HTTP routes. The generator does not edit API registration automatically.

## Generated layout

```text
inventory_api/
├── .env.example           # Development configuration example
├── .gitignore             # Local secrets, caches, and build output
├── docker-compose.yml     # Local PostgreSQL service
├── pyproject.toml         # Dependencies and local CLI entry point
├── main.py                # FastAPI app and service bootstrap
├── app/
│   ├── api/               # API version and route registration
│   ├── config/            # Default, dev, and prod YAML settings
│   ├── core/              # Reusable application backbone
│   ├── features/          # Empty until you add domains
│   └── health.py          # /v1/health route
└── dev_cli/               # Domain, model, and listener generators
```

The copied `app/core` includes settings, dependency injection, domain and entity bases, SQLAlchemy database and repository helpers, transactions, JWT helpers, exceptions, events, logging, and metrics. `main.py` wires the versioned router and core service bootstrap. It contains no application specific runtime services.

## Configuration

Settings are read from `app/config/default.yml`, then the file for `APP_ENV` (such as `dev.yml` or `prod.yml`). Environment variables and `.env` values can override them. Nested environment keys use double underscores, for example `DATABASE__PASSWORD` and `AUTH__TOKENS__SECRET_KEY`.

The template defaults to `APP_ENV=dev` and a PostgreSQL database named after the project. `.env` is ignored by Git; `.env.example` is tracked. Keep production secrets out of YAML files and Git.

## Working on FastKit itself

The installable CLI lives in `fastkit/cli.py`. Files copied into new projects live under `fastkit/template/`. Edits to the template affect **future** generated projects; existing projects are independent copies and are not updated automatically.

To check a local change:

```powershell
uv tool install --reinstall .
fastkit new example_api --destination $env:TEMP --no-git
fastkit generate --project "$env:TEMP\example_api" domain example
```

FastKit currently has no project upgrade command or database migration generator. PostgreSQL is included in the initial template because the copied core's database layer uses it.
