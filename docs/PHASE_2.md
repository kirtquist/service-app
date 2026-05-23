# Phase 2 — Cloud SQL persistence and export

Durable invoice storage on **Cloud SQL PostgreSQL** plus **CSV (QuickBooks)** and **PDF** export for approved invoices.

---

## Database direction

| Environment | Engine | How |
|-------------|--------|-----|
| **Production (Cloud Run)** | **PostgreSQL 15** on Cloud SQL | Pulumi → Secret Manager `database-url` → Cloud Run + Unix socket |
| **Local dev** | SQLite (default) | `sqlite:///./data/service_app.db` when `DATABASE_URL` unset |

**Why PostgreSQL**

- Durable storage (invoices survive deploys)
- Native GCP integration with Cloud Run (`--add-cloudsql-instances`)
- SQLAlchemy + future Alembic migrations
- Standard choice before QuickBooks API (Phase 3)

Pulumi creates:

| Resource | ID / name |
|----------|-----------|
| Cloud SQL instance | `service-app-db` |
| Database | `service_app` |
| User | `service_app` |
| Secret | `database-url` (full SQLAlchemy URL) |
| IAM | Runtime SA → `roles/cloudsql.client` + secret accessor |

---

## Pulumi setup

```bash
cd infra
pulumi stack select prod
pulumi config set --secret webAuthPassword "YOUR_WEB_PASSWORD"   # if not done
pulumi up
```

Outputs:

```bash
pulumi stack output cloud_sql_connection_name
pulumi stack output database_url_secret_id
```

**Must match** GitHub Actions env `CLOUD_SQL_INSTANCE` in `.github/workflows/deploy-cloud-run.yml`.

Optional config (`Pulumi.prod.yaml`):

| Key | Default |
|-----|---------|
| `databaseName` | `service_app` |
| `databaseUser` | `service_app` |
| `databaseTier` | `db-f1-micro` |
| `databaseInstanceName` | `service-app-db` |

Password is auto-generated (`pulumi-random`) and stored only in Secret Manager via the connection URL.

---

## Export (QuickBooks + PDF)

Available on **approved** invoices only.

| Export | URL | Use |
|--------|-----|-----|
| **CSV** | `/app/invoices/{id}/export.csv` | QuickBooks Online import / bookkeeper |
| **PDF** | `/app/invoices/{id}/export.pdf` | Customer copy or office records |

CSV columns:

`Invoice Number`, `Customer`, `Invoice Date`, `Product/Service`, `Description`, `Quantity`, `Rate`, `Amount`

- Labor → row with Product/Service `Labor`
- Parts → rows with Product/Service `Parts`

Invoice numbers: `INV-0001`, `INV-0002`, …

---

## Local dev

SQLite (no Cloud SQL required):

```bash
service-app-api
open http://127.0.0.1:8090/app/invoices
```

Optional local Postgres:

```bash
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/service_app
```

---

## Deploy checklist

1. `pulumi up` (creates Cloud SQL + `database-url` secret)
2. Merge `feature/phase-2-cloud-sql-export` → `dev`
3. GitHub Action deploys with:
   - `DATABASE_URL=database-url:latest`
   - `--add-cloudsql-instances=kgs-service-app:us-west1:service-app-db`
4. First request creates tables (`create_all`)

**Note:** Invoices from the old `/tmp` SQLite era are **not** migrated automatically.

---

## Next (Phase 3)

QuickBooks Online API — OAuth, push approved invoices, sync metadata.

See [`VISION.md`](VISION.md).
