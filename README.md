# Scaffoldlane

Scaffoldlane is an installable CLI for starting FastAPI projects with a reusable application backbone. It copies a template containing configuration, dependency injection, PostgreSQL data access, email/password signup and signin, logging, a versioned API, and feature generators. New projects include only the generic `auth` feature under `app/features`. The source application's company, vehicle, Telegram, and other business features are not included.

Scaffoldlane currently creates projects and generates feature code.

Optional integrations can be added to generated projects with `scaffoldlane add`.

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/) to follow these commands. You can also install the CLI with `pipx`.
- Git for the default repository initialization. Use `--no-git` if Git is unavailable.
- Docker with Compose if you want to run the provided PostgreSQL service.

## Install the CLI

After publishing to PyPI:

```powershell
uv tool install scaffoldlane
scaffoldlane --help
```

Alternatively, install in a Python environment with `python -m pip install scaffoldlane`. The `scaffoldlane` executable is then available in that environment's scripts directory.

For local development, from this repository's `fastkit` directory:

```powershell
uv tool install .
scaffoldlane --help
```

After changing the local CLI or template, run `uv tool install --reinstall .`. If PowerShell reports that `scaffoldlane` is not recognized, add uv's tool directory to the current terminal's `PATH`:

```powershell
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
scaffoldlane --help
```

Run `uv tool update-shell` and open a new terminal to make the tool directory available in future sessions.

The PyPI distribution name and CLI command are both `scaffoldlane`. Earlier releases under `fastkit-project-generator` are separate and are not updated by publishing this package.

## Publish a release

From this repository's `fastkit` directory, update the version in `pyproject.toml`, then build and inspect the distributions before uploading:

```powershell
uv build --no-sources --out-dir dist/scaffoldlane
uv publish dist/scaffoldlane/scaffoldlane-0.1.0-py3-none-any.whl dist/scaffoldlane/scaffoldlane-0.1.0.tar.gz
```

`uv publish` needs a PyPI token or configured trusted publishing. Each published version is immutable; increment the version for later releases.

## Create a project

Run this from the directory in which you want the new project folder:

```powershell
scaffoldlane new inventory_api
cd inventory_api
```

The name must start with a lowercase letter and may contain lowercase letters, digits, and underscores. Scaffoldlane will not overwrite an existing folder.

`new` copies the bundled template, replaces the project-name placeholders, and initializes a Git repository. It does not create a Git commit or install the generated project's dependencies.

```powershell
scaffoldlane new inventory_api --destination C:\projects
scaffoldlane new inventory_api --no-git
scaffoldlane new --help
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

The default auth routes are `POST /v1/auth/signup` and `POST /v1/auth/signin`. Both accept JSON with `email` and `password`; signin returns a bearer access token. The feature has `data/repositories`, `domain/entities`, `domain/repositories`, `domain/services`, `domain/usecases`, `presentation/routes`, and `presentation/schema` packages. The repository maps database rows directly to domain entities. The bundled PostgreSQL container runs `db/migrations/001_users.sql` when its data volume is first created. Apply that SQL yourself for an existing or remote database. Set a unique `AUTH__TOKENS__SECRET_KEY` of at least 32 bytes in `.env` before issuing tokens. The auth feature does not include password reset or email verification; add those when your project needs them.

The example `.env` contains development credentials and a placeholder token secret. Replace them before using the project outside local development. The health route can run without an active PostgreSQL connection, but database features need the Compose service or another configured PostgreSQL instance.

## Add Redis

From a generated project directory, run:

```powershell
scaffoldlane add redis
uv sync
docker compose up -d redis
```

Or use `scaffoldlane add redis --project .\inventory_api` from another directory. The command adds `app/core/redis/connection.py` and `kv_service.py`, Redis settings, a Compose service, the `redis` Python dependency, and startup/shutdown wiring. It refuses to overwrite an existing Redis integration. Configure a remote Redis instance with `REDIS__HOST`, `REDIS__PORT`, `REDIS__DB`, and `REDIS__PASSWORD` in `.env`; the bundled Compose service is intended for local development without a password.

`MainRedisConnection` connects in a background retry loop, so application startup does not wait for Redis. Check `is_connected` if a feature needs to report readiness. Inject `RedisKVService` for common key-value operations, or `MainRedisConnection` for direct Redis commands. The service manager owns connection shutdown.

Future optional integrations belong under `scaffoldlane/addons/<name>/`, with their own installer and copied files. The `scaffoldlane add` command group keeps these separate from feature/domain generation.

## Add Socket.IO

From a generated project directory, run:

```powershell
scaffoldlane add socketio
uv sync
uv run python main.py
```

This adds `app/socketio/instance.py` with a shared asynchronous Socket.IO server, generic emit helpers in `app/socketio/emitter.py`, and the `python-socketio` dependency. The installer wraps the FastAPI application as `sio_app = ASGIApp(sio, other_asgi_app=app)` and runs `main:sio_app` on port `5010` when `main.py` is launched directly. You can also run `uv run uvicorn main:sio_app --host 0.0.0.0 --port 5010 --reload`.

The `app/socketio/events/` package contains an inactive example handler. Add your handlers there and call their registration functions from `app/socketio/register.py`; `main.py` calls `register_all_events(sio)` during setup. To try the example, uncomment its two lines in `register.py`. No project-specific connection tracking is installed. The default server keeps client state in the current process; configure a Socket.IO client manager yourself if you need multiple workers or instances. Set `cors_allowed_origins` in `instance.py` to your permitted frontend origins before deployment.

## Add authorization

From a generated project directory, run `scaffoldlane add authorization`. The command copies a generic role-based access manager, a PostgreSQL repository, a FastAPI dependency, and `db/migrations/authorization.sql`. It does not run the SQL. Review and apply the migration after `001_users.sql`; `user_roles.user_id` references the default `users` table. The schema assumes UUID user IDs, matching `get_current_user_id` in the base template.

Create your project's permissions, roles, grants, and user assignments after applying the migration. No business-specific resources or role seeds are included. Protect a route with `dependencies=[Depends(require_permission("invoice", "read"))]`, importing `Depends` from FastAPI and `require_permission` from `app.core.authorization.dependency`. For checks in use cases, call `await injector.get(AccessManager).require(user_id=user_id, resource="invoice", action="read")`.

The singleton access manager caches active role grants, while it fetches the user's current role IDs for each decision. Call `await injector.get(AccessManager).invalidate_grants()` after changing a role, permission, or grant. User role assignments take effect on the next check without invalidation. The cache is per process: projects running multiple workers must also invalidate or refresh the other workers after grant changes. A project with different identity storage can implement `AccessRepository` instead of using the included SQL repository.

## Add tracing

From a generated project directory, run:

```powershell
scaffoldlane add tracing
uv sync
```

This adds OpenTelemetry configuration, tracing bootstrap, repository spans, and trace-aware structured logging. Tracing starts disabled; set `TRACING__ENABLED=true` and `TRACING__OTLP_TRACES_ENDPOINT` in `.env` to export traces. You can also set `TRACING__SERVICE_NAME`. If Redis is installed, its key-value service gains Redis spans. Redis and tracing can be added in either order. New projects have no OpenTelemetry dependency until tracing is added.

## Generate features

From the generated project directory:

```powershell
scaffoldlane generate domain product
scaffoldlane generate model product item
scaffoldlane generate listener product product_created
```

From another directory, point the CLI at the project:

```powershell
scaffoldlane generate --project .\inventory_api domain product
```

`generate domain` creates data, domain, and presentation folders with a domain repository interface and data repository implementation. It does not create DTOs. `generate model` adds a domain entity to an existing domain. `generate listener` adds a listener to an existing domain; use `--event module.path:EventClass` to select its event class. The generators accept `--force` to overwrite generated files. Inspect existing code before using that option.

Scaffoldlane delegates generation to the generated project's `dev_cli` package, so each project's generator matches the template version it was created with. Run `scaffoldlane generate --project PATH --help` or `scaffoldlane generate --project PATH domain --help` for command options.

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

## Working on Scaffoldlane itself

The installable CLI lives in `scaffoldlane/cli.py`. Files copied into new projects live under `scaffoldlane/template/`. Edits to the template affect **future** generated projects; existing projects are independent copies and are not updated automatically.

To check a local change:

```powershell
uv tool install --reinstall .
scaffoldlane new example_api --destination $env:TEMP --no-git
scaffoldlane generate --project "$env:TEMP\example_api" domain example
```

Scaffoldlane currently has no project upgrade command or database migration generator. PostgreSQL is included in the initial template because the copied core's database layer uses it.
