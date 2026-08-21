## Context

The repository manages GCP infrastructure using OpenTofu/Terraform under `infra/gcp/`. The `shareabouts-service` module (`infra/gcp/modules/shareabouts-service/`) defines common resources for Cloud Run services, Cloud SQL connectivity via Serverless VPC Access Connector, Secret Manager secrets, IAM service accounts, and a `migrate` Cloud Run Job (`jobs.tf`).

Environments (`dev`, `prod`) instantiate this module in `infra/gcp/envs/<env>/main.tf`. Local variable inputs are commonly loaded from `.auto.tfvars` (which is excluded from Git via `.gitignore`).

See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Provide optional variable inputs for `superuser_username`, `superuser_email`, and `superuser_password` (all default `null`).
- Conditionally provision Secret Manager secrets and IAM bindings for superuser credentials only when all three variables are non-null.
- Conditionally provision a Cloud Run Job named `${service_name}-${environment}-createsuperuser` that executes `python manage.py createsuperuser --noinput` against the environment database.
- Allow running the job on-demand via `gcloud run jobs execute <job-name> --region <region>`.

**Non-Goals:**
- Automatically executing the `createsuperuser` job during `tofu apply` (it is an on-demand administrative task).
- Generating random fallback passwords in Terraform (credentials must be explicitly provided by the user).
- Implementing custom idempotent Django management commands (stock Django command behavior is expected).

## Decisions

### 1. Three Dedicated Secret Manager Secrets
* **Decision**: Create three distinct Secret Manager secrets per environment:
  - `${var.service_name}-${var.environment}-superuser-username`
  - `${var.service_name}-${var.environment}-superuser-email`
  - `${var.service_name}-${var.environment}-superuser-password`
* **Rationale**: Follows the established secret pattern in `main.tf` (`db_password`, `secret_key`) and allows clean, direct mapping via Cloud Run `secret_key_ref` into standard Django environment variables (`DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`).
* **Alternative Considered**: Storing username and email as plaintext container env vars and only password in Secret Manager. Rejected in favor of managing all superuser credentials securely and consistently via Secret Manager.

### 2. All-or-Nothing Conditionality
* **Decision**: Evaluate `local.enable_createsuperuser = var.superuser_username != null && var.superuser_email != null && var.superuser_password != null`.
* **Rationale**: Django's `createsuperuser --noinput` requires username, email, and password to be present simultaneously. Provisioning secrets or the job if any variable is missing would result in a broken job.
* **Alternative Considered**: Allowing partial configuration with fallback defaults (e.g., defaulting username to "admin"). Rejected because explicit configuration avoids accidental provisioning.

### 3. Cloud Run Job Structure in `jobs.tf`
* **Decision**: Use `count = local.enable_createsuperuser ? 1 : 0` on the `google_cloud_run_v2_job.createsuperuser` resource and its corresponding IAM secret accessor bindings.
* **Rationale**: Reuses the same Service Account (`google_service_account.sa.email`), VPC Access Connector, database environment variables (`local.env_vars`), and database secret references (`local.env_secrets`), while adding dynamic secret references for the superuser environment variables.

## Risks / Trade-offs

- **[Duplicate user failure on rerun]** → If the job is executed when a user with that username already exists, Django raises `CommandError: That username is already taken.`. Mitigation: Standard expected behavior; job is run on-demand when creating a superuser.
- **[Secret exposure in tfvars]** → Storing plaintext passwords in `.auto.tfvars`. Mitigation: `superuser_password` variable is marked `sensitive = true` and `.auto.tfvars` is ignored by `.gitignore`.
