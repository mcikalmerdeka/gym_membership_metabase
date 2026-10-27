# Docker Setup Reminder

Quick reference for the local PostgreSQL + Metabase stack in this project.

Run all commands from the repository root:

```text
E:\Personal Projects\Gym Membership Metabase
```

## What runs

| Container | Purpose | Host access |
|---|---|---|
| `gym-postgres` | Gym data and Metabase application data | `localhost:5433` |
| `gym-metabase` | Metabase web application | <http://localhost:3000> |

PostgreSQL contains two separate databases:

- `gym` - the analysis-ready gym tables.
- `metabase` - Metabase's own application data (users, questions, dashboards, settings).

Do not point Metabase at the `metabase` database for gym analysis. Use `gym`.

## Prerequisites

- Docker Desktop is installed and running with Linux containers.
- Port `3000` is free for Metabase.
- Host port `5433` is free for PostgreSQL. Port `5432` is usually taken by a local PostgreSQL installation, so this project uses `5433` on the host.
- Inside Docker, Metabase still connects to PostgreSQL on the standard `postgres:5432`.

## First-time startup

```bash
docker compose up -d
docker compose ps
```

The first run pulls the container images and can take a few minutes. Check
progress with:

```bash
docker compose logs -f postgres
docker compose logs -f metabase
```

Wait until `gym-postgres` is `healthy` and Metabase responds at
<http://localhost:3000>. Metabase can take 1-2 minutes to initialize.

## Metabase first-time setup

1. Open <http://localhost:3000>.
2. Create the first admin account.
3. Add a database connection with:

| Setting | Value |
|---|---|
| Display name | Gym Membership |
| Host | `postgres` |
| Port | `5432` |
| Database name | `gym` |
| Username | `gym_admin` |
| Password | `gym_password` |
| SSL | Off (local only) |

Use `postgres` as the host because Metabase and PostgreSQL are separate
containers. Use `localhost:5433` only when connecting from tools running on
Windows, such as DBeaver or pgAdmin.

## Data loaded on first startup

The initialization scripts live in `docker/init/`:

- `01-create-metabase-db.sql` creates the separate `metabase` database.
- `02-load-gym-data.sh` runs `sql/analysis_ready_schema.sql` against the `gym` database.

The Compose file mounts these paths for the first load:

| Host path | Container path |
|---|---|
| `docker/init/` | `/docker-entrypoint-initdb.d/` |
| `data/analysis_ready/` | `/workspace/data/analysis_ready/` |
| `sql/` | `/workspace/sql/` |

The `gym` database contains:

| Table | Rows |
|---|---:|
| `gym_members_clean` | 1,000 |
| `gym_members_wide` | 1,000 |
| `gym_member_days` | 2,682 |
| `gym_member_lessons` | 1,003 |
| `gym_member_drinks` | 719 |

Check them with:

```bash
docker compose exec -T postgres psql -U gym_admin -d gym -c "\dt"
```

## Rebuild and reload the data

If you regenerate the analysis-ready CSVs:

```bash
uv run python scripts/build_analysis_ready.py
uv run pytest -q
docker compose exec -T postgres sh -c "cd /workspace && psql -U gym_admin -d gym -f sql/analysis_ready_schema.sql"
```

The SQL uses `TRUNCATE` before `COPY`, so it replaces the existing table
contents instead of creating duplicates.

## Daily commands

```bash
docker compose up -d          # start in the background
docker compose ps             # check status and ports
docker compose stop           # stop without removing containers
docker compose start          # start existing containers again
docker compose restart        # restart the stack
docker compose down           # stop and remove containers/network, keep data
docker compose logs -f        # follow logs for all services
docker compose logs -f metabase
docker compose logs -f postgres
```

## Data persistence and backups

Your Metabase users, questions, dashboards, and settings live in the
`metabase` database inside the PostgreSQL data volume. `docker compose up -d`
and `docker compose down` do not delete that volume.

The initialization scripts in `docker/init/` run only when the PostgreSQL data
directory is empty. They will not re-run on a normal restart, so they will not
reload or truncate existing data.

Safe operations:

- `docker compose up -d`
- `docker compose restart`
- `docker compose down` (keeps volumes)
- Adding a new service such as Adminer and running `docker compose up -d`

Destructive operations:

- `docker compose down -v`
- Deleting the Compose project's PostgreSQL or Metabase volumes
- Changing `POSTGRES_USER` or `POSTGRES_PASSWORD` after the first
  initialization. The database keeps the original credentials, so Metabase
  may lose access even though the data still exists.

Back up the Metabase application database before risky changes:

```bash
docker compose exec -T postgres sh -c "pg_dump -U gym_admin -d metabase -Fc -f /tmp/metabase.dump"
docker compose cp postgres:/tmp/metabase.dump ./metabase.dump
```

Back up the gym database:

```bash
docker compose exec -T postgres sh -c "pg_dump -U gym_admin -d gym -Fc -f /tmp/gym.dump"
docker compose cp postgres:/tmp/gym.dump ./gym.dump
```

If you overrode `POSTGRES_USER`, replace `gym_admin` in the commands above.

## Health checks

Metabase:

```powershell
Invoke-RestMethod http://localhost:3000/api/health
```

Expected response:

```json
{"status":"ok"}
```

PostgreSQL:

```bash
docker compose exec -T postgres pg_isready -U gym_admin -d gym
```

## Reset everything

This deletes the PostgreSQL data volume and the Metabase application volume,
then recreates both databases and reloads the gym data on the next startup:

```bash
docker compose down -v
docker compose up -d
```

Only use `-v` when you are comfortable losing Metabase questions, dashboards,
users, and settings.

## Troubleshooting

### Port 5432 is already in use

That is expected on this machine. The Docker database is exposed on host port
`5433`:

```text
localhost:5433 -> gym-postgres:5432
```

Inside Metabase, use host `postgres` and port `5432`.

### Port 3000 is already in use

Set a different host port before starting:

```powershell
$env:METABASE_PORT = "3001"
docker compose up -d
```

Then open <http://localhost:3001>. Update `MB_SITE_URL` too if needed:

```powershell
$env:MB_SITE_URL = "http://localhost:3001"
```

### Metabase returns 503 during startup

Wait 1-2 minutes and check again. The health endpoint is expected to return
503 while Metabase is still initializing.

### Data did not load

Check the Postgres initialization logs:

```bash
docker compose logs postgres
```

If the volume was initialized before the loader existed, either run the manual
reload command above or reset with `docker compose down -v` and start again.

### Metabase cannot connect to `gym`

- Host must be `postgres`, not `localhost`.
- Port must be `5432`, not `5433`.
- Database must be `gym`.
- Use the same `POSTGRES_USER` and `POSTGRES_PASSWORD` shown in
  `docker-compose.yml` unless you overrode them.

## Local-only credentials

The defaults in `docker-compose.yml` are for local development only:

```text
Database: gym
Username: gym_admin
Password: gym_password
```

Override them through your shell or a `.env` file before exposing the stack
outside your machine. Do not publish this stack to the internet with the
default credentials.

## Related files

- `docker-compose.yml` - container definitions, ports, volumes, healthcheck.
- `docker/init/01-create-metabase-db.sql` - creates the Metabase application database.
- `docker/init/02-load-gym-data.sh` - loads the gym tables on first initialization.
- `sql/analysis_ready_schema.sql` - table DDL and `\copy` load commands.
- `data/analysis_ready/` - the five generated CSV files.
- `data/analysis_ready/data_dictionary.md` - column definitions and data rules.
- `scripts/build_analysis_ready.py` - rebuilds the analysis-ready CSVs.
