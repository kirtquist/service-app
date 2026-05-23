"""Pulumi stack — GCP foundation for service-app Cloud Run API.

Creates APIs, Artifact Registry, secrets, Cloud SQL Postgres, runtime + GitHub
deploy service accounts, and IAM. Cloud Run *deployments* stay in GitHub Actions.
"""

import base64
from urllib.parse import quote_plus

import pulumi
import pulumi_gcp as gcp
import pulumi_random as random

config = pulumi.Config()
gcp_config = pulumi.Config("gcp")

project = gcp_config.require("project")
region = gcp_config.get("region") or "us-west1"
openrouter_api_key = config.require_secret("openrouterApiKey")
web_auth_username = config.get("webAuthUsername") or "admin"
web_auth_password = config.get_secret("webAuthPassword")
database_name = config.get("databaseName") or "service_app"
database_user = config.get("databaseUser") or "service_app"
database_tier = config.get("databaseTier") or "db-f1-micro"
database_instance_name = config.get("databaseInstanceName") or "service-app-db"

REQUIRED_APIS = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "sqladmin.googleapis.com",
    "compute.googleapis.com",
]

enabled_apis: list[gcp.projects.Service] = []
for api in REQUIRED_APIS:
    enabled_apis.append(
        gcp.projects.Service(
            api.replace(".", "-"),
            project=project,
            service=api,
            disable_on_destroy=False,
        )
    )

artifact_registry = gcp.artifactregistry.Repository(
    "service-app",
    project=project,
    location=region,
    repository_id="service-app",
    description="Service App API container images",
    format="DOCKER",
    opts=pulumi.ResourceOptions(depends_on=enabled_apis),
)

openrouter_secret = gcp.secretmanager.Secret(
    "openrouter-api-key",
    project=project,
    secret_id="openrouter-api-key",
    replication=gcp.secretmanager.SecretReplicationArgs(
        auto=gcp.secretmanager.SecretReplicationAutoArgs(),
    ),
    opts=pulumi.ResourceOptions(depends_on=enabled_apis),
)

gcp.secretmanager.SecretVersion(
    "openrouter-api-key-v1",
    secret=openrouter_secret.id,
    secret_data=openrouter_api_key,
)

runtime_sa = gcp.serviceaccount.Account(
    "service-app-api",
    account_id="service-app-api",
    display_name="Service App Cloud Run runtime",
    project=project,
)

gcp.secretmanager.SecretIamMember(
    "runtime-openrouter-secret-accessor",
    project=project,
    secret_id=openrouter_secret.secret_id,
    role="roles/secretmanager.secretAccessor",
    member=pulumi.Output.concat("serviceAccount:", runtime_sa.email),
)

web_auth_secret = None
if web_auth_password is not None:
    web_auth_secret = gcp.secretmanager.Secret(
        "web-auth-password",
        project=project,
        secret_id="web-auth-password",
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(depends_on=enabled_apis),
    )

    gcp.secretmanager.SecretVersion(
        "web-auth-password-v1",
        secret=web_auth_secret.id,
        secret_data=web_auth_password,
    )

    gcp.secretmanager.SecretIamMember(
        "runtime-web-auth-secret-accessor",
        project=project,
        secret_id=web_auth_secret.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", runtime_sa.email),
    )

# --- Cloud SQL (PostgreSQL) for durable invoice storage ---

db_password = random.RandomPassword(
    "database-password",
    length=32,
    special=False,
)

db_instance = gcp.sql.DatabaseInstance(
    "service-app-db",
    name=database_instance_name,
    database_version="POSTGRES_15",
    region=region,
    deletion_protection=False,
    settings=gcp.sql.DatabaseInstanceSettingsArgs(
        tier=database_tier,
        edition="ENTERPRISE",
        ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
            ipv4_enabled=False,
        ),
        backup_configuration=gcp.sql.DatabaseInstanceSettingsBackupConfigurationArgs(
            enabled=True,
            point_in_time_recovery_enabled=False,
        ),
    ),
    opts=pulumi.ResourceOptions(depends_on=enabled_apis),
)

gcp.sql.Database(
    "service-app-database",
    name=database_name,
    instance=db_instance.name,
    opts=pulumi.ResourceOptions(depends_on=[db_instance]),
)

gcp.sql.User(
    "service-app-db-user",
    name=database_user,
    instance=db_instance.name,
    password=db_password.result,
    opts=pulumi.ResourceOptions(depends_on=[db_instance]),
)

database_url_secret = gcp.secretmanager.Secret(
    "database-url",
    project=project,
    secret_id="database-url",
    replication=gcp.secretmanager.SecretReplicationArgs(
        auto=gcp.secretmanager.SecretReplicationAutoArgs(),
    ),
    opts=pulumi.ResourceOptions(depends_on=enabled_apis),
)

database_url = pulumi.Output.all(db_password.result, db_instance.connection_name).apply(
    lambda args: (
        f"postgresql+psycopg2://{database_user}:{quote_plus(args[0])}"
        f"@/{database_name}?host=/cloudsql/{args[1]}"
    )
)

gcp.secretmanager.SecretVersion(
    "database-url-v1",
    secret=database_url_secret.id,
    secret_data=database_url,
)

gcp.secretmanager.SecretIamMember(
    "runtime-database-url-secret-accessor",
    project=project,
    secret_id=database_url_secret.secret_id,
    role="roles/secretmanager.secretAccessor",
    member=pulumi.Output.concat("serviceAccount:", runtime_sa.email),
)

gcp.projects.IAMMember(
    "runtime-cloudsql-client",
    project=project,
    role="roles/cloudsql.client",
    member=pulumi.Output.concat("serviceAccount:", runtime_sa.email),
)

github_sa = gcp.serviceaccount.Account(
    "github-deploy",
    account_id="github-deploy",
    display_name="GitHub Actions deploy",
    project=project,
)

for role in ("roles/run.admin", "roles/artifactregistry.writer"):
    gcp.projects.IAMMember(
        f"github-{role.split('/')[-1]}",
        project=project,
        role=role,
        member=pulumi.Output.concat("serviceAccount:", github_sa.email),
    )

gcp.serviceaccount.IAMMember(
    "github-act-as-runtime-sa",
    service_account_id=runtime_sa.name,
    role="roles/iam.serviceAccountUser",
    member=pulumi.Output.concat("serviceAccount:", github_sa.email),
)

github_key = gcp.serviceaccount.Key(
    "github-deploy-key",
    service_account_id=github_sa.name,
)

image_repo = pulumi.Output.concat(
    region,
    "-docker.pkg.dev/",
    project,
    "/service-app",
)

pulumi.export("project_id", project)
pulumi.export("region", region)
pulumi.export("artifact_registry_repository", image_repo)
pulumi.export("runtime_service_account_email", runtime_sa.email)
pulumi.export("web_auth_username", web_auth_username)
if web_auth_secret is not None:
    pulumi.export("web_auth_password_secret_id", web_auth_secret.secret_id)
else:
    pulumi.export("web_auth_password_secret_id", "")
pulumi.export("cloud_sql_instance_name", db_instance.name)
pulumi.export("cloud_sql_connection_name", db_instance.connection_name)
pulumi.export("database_name", database_name)
pulumi.export("database_user", database_user)
pulumi.export("database_url_secret_id", database_url_secret.secret_id)
pulumi.export("github_deploy_service_account_email", github_sa.email)
pulumi.export(
    "github_deploy_sa_key_json",
    pulumi.Output.secret(
        github_key.private_key.apply(lambda encoded: base64.b64decode(encoded).decode("utf-8"))
    ),
)
pulumi.export(
    "next_steps",
    pulumi.Output.concat(
        "Run `pulumi up`, then merge feature/phase-2 to dev to deploy Cloud Run with ",
        "`--add-cloudsql-instances=", db_instance.connection_name, "`.",
    ),
)
