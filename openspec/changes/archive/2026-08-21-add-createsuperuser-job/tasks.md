## 1. Module Variables and Conditionals

- [x] 1.1 Add `superuser_username`, `superuser_email`, and `superuser_password` optional variables to `infra/gcp/modules/shareabouts-service/variables.tf` (defaulting to `null`, password marked sensitive).
- [x] 1.2 Add `enable_createsuperuser` local condition to `infra/gcp/modules/shareabouts-service/main.tf`.

## 2. Superuser Secrets and IAM in Module

- [x] 2.1 Add conditional `google_secret_manager_secret` and `google_secret_manager_secret_version` resources for superuser username, email, and password in `infra/gcp/modules/shareabouts-service/main.tf`.
- [x] 2.2 Add conditional `google_secret_manager_secret_iam_member` resources granting `roles/secretmanager.secretAccessor` to the Cloud Run service account for the superuser secrets in `infra/gcp/modules/shareabouts-service/main.tf`.

## 3. Cloud Run Createsuperuser Job

- [x] 3.1 Add conditional `google_cloud_run_v2_job.createsuperuser` resource to `infra/gcp/modules/shareabouts-service/jobs.tf` configured to run `python manage.py createsuperuser --noinput`.
- [x] 3.2 Map database environment variables and map `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` from Secret Manager into the job container.

## 4. Environment Wiring

- [x] 4.1 Add `superuser_username`, `superuser_email`, and `superuser_password` variables to `infra/gcp/envs/dev/variables.tf` and pass them to the module in `infra/gcp/envs/dev/main.tf`.
- [x] 4.2 Add `superuser_username`, `superuser_email`, and `superuser_password` variables to `infra/gcp/envs/prod/variables.tf` and pass them to the module in `infra/gcp/envs/prod/main.tf`.

## 5. Verification

- [x] 5.1 Format and validate OpenTofu/Terraform configurations across the module and environment directories.

