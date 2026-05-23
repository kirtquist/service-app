"""Pulumi stack — GCP foundation for service-app Cloud Run API.

Creates APIs, Artifact Registry, OpenRouter secret, runtime + GitHub deploy
service accounts, and IAM. Cloud Run *deployments* stay in GitHub Actions
(build/push image on each merge to dev/main).
"""

import base64

import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
gcp_config = pulumi.Config("gcp")

project = gcp_config.require("project")
region = gcp_config.get("region") or "us-west1"
openrouter_api_key = config.require_secret("openrouterApiKey")
web_auth_username = config.get("webAuthUsername") or "admin"
web_auth_password = config.get_secret("webAuthPassword")

REQUIRED_APIS = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    # Pulumi GCP provider lists regions via Compute API (warning if disabled).
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
        "Add GitHub secret GCP_SA_KEY from `pulumi stack output github_deploy_sa_key_json --show-secrets`, ",
        "then merge to dev/main to trigger Cloud Run deploy.",
    ),
)
