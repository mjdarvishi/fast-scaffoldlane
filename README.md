# FastKit

FastKit is an installable CLI for starting FastAPI projects with a reusable application backbone. It copies a template containing configuration, dependency injection, PostgreSQL data access, authentication helpers, logging, tracing hooks, a versioned API, and feature generators. New projects have an empty `app/features` package. The source application's company, vehicle, Telegram, and other business features are not included.

FastKit currently creates projects and generates feature code.

## Requirements

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/) to follow these commands. You can also install the CLI with `pipx`.
- Git for the default repository initialization. Use `--no-git` if Git is unavailable.
- Docker with Compose if you want to run the provided PostgreSQL service.

## Install the CLI

From this repository's `fastkit` directory:

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

**Publishing note:** `fastkit` is already used by an unrelated [PyPI package](https://pypi.org/project/fastkit/). These instructions install this repository's local package. A distinct distribution name will be needed before publishing this project to PyPI.

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

The copied `app/core` includes settings, dependency injection, domain and entity bases, SQLAlchemy database and repository helpers, transactions, JWT helpers, exceptions, events, logging, metrics, and optional tracing support. `main.py` wires the versioned router and core service bootstrap. It contains no application specific runtime services.

## Configuration

Settings are read from `app/config/default.yml`, then the file for `APP_ENV` (such as `dev.yml` or `prod.yml`). Environment variables and `.env` values can override them. Nested environment keys use double underscores, for example `DATABASE__PASSWORD` and `AUTH__TOKENS__SECRET_KEY`.

The template defaults to `APP_ENV=dev`, a PostgreSQL database named after the project, and disabled tracing. `.env` is ignored by Git; `.env.example` is tracked. Keep production secrets out of YAML files and Git.

## Working on FastKit itself

The installable CLI lives in `fastkit/cli.py`. Files copied into new projects live under `fastkit/template/`. Edits to the template affect **future** generated projects; existing projects are independent copies and are not updated automatically.

To check a local change:

```powershell
uv tool install --reinstall .
fastkit new example_api --destination $env:TEMP --no-git
fastkit generate --project "$env:TEMP\example_api" domain example
```

FastKit currently has no project upgrade command or database migration generator. PostgreSQL is included in the initial template because the copied core's database layer uses it.
