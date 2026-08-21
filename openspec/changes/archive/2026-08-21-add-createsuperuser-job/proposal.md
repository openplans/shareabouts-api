## Why

Provisioning initial administrative access on deployed GCP environments (dev, prod) currently requires manual database access or ad-hoc interventions. By defining a dedicated Cloud Run Job in our OpenTofu/Terraform configuration similar to the database migration job, administrators can safely and reproducibly execute `createsuperuser` without exposing direct database ports or storing hardcoded credentials.

## What Changes

- Add optional input variables for `superuser_username`, `superuser_email`, and `superuser_password` (all default to `null`) to the `shareabouts-service` Terraform module and environment configurations (`dev`, `prod`).
- Conditionally create GCP Secret Manager secrets for the superuser username, email, and password when all three variables are supplied.
- Conditionally provision a Cloud Run Job (`${service_name}-${environment}-createsuperuser`) that runs `python manage.py createsuperuser --noinput` with database configuration and superuser secrets mapped as environment variables (`DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`).
- Ensure the Cloud Run Service Account has `roles/secretmanager.secretAccessor` permissions to read the new superuser secrets.

## Capabilities

### New Capabilities
- `gcp-createsuperuser-job`: Defines the provisioning and execution of the Django `createsuperuser` Cloud Run Job and associated Secret Manager secrets across GCP environments when configured.

### Modified Capabilities

## Impact

- **Infrastructure**: Updates `infra/gcp/modules/shareabouts-service/` (`variables.tf`, `jobs.tf`, `main.tf` if needed) and environment configs (`infra/gcp/envs/dev/`, `infra/gcp/envs/prod/`).
- **Secret Management**: Creates up to 3 optional secrets per environment in GCP Secret Manager.
- **Operations**: Enables triggering superuser creation via `gcloud run jobs execute <service>-<env>-createsuperuser --region <region>`.
- **Breaking Changes**: None. Variables default to `null`, preserving existing behavior when omitted.
