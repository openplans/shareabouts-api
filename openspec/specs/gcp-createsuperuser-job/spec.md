# gcp-createsuperuser-job Specification

## Purpose
Provides infrastructure provisioning and execution capabilities for creating a Django superuser in GCP environments via a Cloud Run Job.

## Requirements

### Requirement: Optional Superuser Variable Configuration
The infrastructure module and environment configurations SHALL define `superuser_username`, `superuser_email`, and `superuser_password` variables that are optional and default to `null`.

#### Scenario: All superuser variables omitted
- **WHEN** none of `superuser_username`, `superuser_email`, and `superuser_password` are provided in `.auto.tfvars` or module inputs
- **THEN** all three variables default to `null` and superuser provisioning is disabled

#### Scenario: All superuser variables provided
- **WHEN** `superuser_username`, `superuser_email`, and `superuser_password` are all provided with non-null values
- **THEN** superuser provisioning is enabled for that environment

#### Scenario: Partial superuser variables provided
- **WHEN** only one or two of `superuser_username`, `superuser_email`, or `superuser_password` are provided
- **THEN** superuser provisioning is not enabled

### Requirement: Conditional Superuser Secret Creation
The infrastructure module SHALL provision GCP Secret Manager secrets for the superuser credentials if and only if all three superuser variables are provided.

#### Scenario: Secrets created when superuser credentials are provided
- **WHEN** superuser credentials (`superuser_username`, `superuser_email`, and `superuser_password`) are provided
- **THEN** Secret Manager secrets and secret versions are created for `${service_name}-${environment}-superuser-username`, `${service_name}-${environment}-superuser-email`, and `${service_name}-${environment}-superuser-password`
- **THEN** the Cloud Run Service Account is granted `roles/secretmanager.secretAccessor` permission on each superuser secret

#### Scenario: Secrets omitted when superuser credentials are null
- **WHEN** any superuser credential variable is null
- **THEN** no superuser Secret Manager secrets or IAM bindings are created

### Requirement: Conditional Cloud Run Createsuperuser Job Provisioning
The infrastructure module SHALL provision a Cloud Run Job named `${service_name}-${environment}-createsuperuser` if and only if all three superuser variables are provided.

#### Scenario: Job created when superuser credentials are provided
- **WHEN** all superuser credential variables are non-null
- **THEN** a Cloud Run Job named `${service_name}-${environment}-createsuperuser` is provisioned
- **THEN** the job runs `python manage.py createsuperuser --noinput`
- **THEN** the job is configured with the environment's VPC connector, Cloud SQL permissions, database environment variables, and superuser secrets mapped to `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD`

#### Scenario: Job omitted when superuser credentials are null
- **WHEN** any superuser credential variable is null
- **THEN** the Cloud Run createsuperuser job is not created

### Requirement: Superuser Job Execution
When triggered on GCP, the `createsuperuser` Cloud Run Job SHALL execute `python manage.py createsuperuser --noinput` against the environment database using the configured secrets.

#### Scenario: Successful execution on empty user database
- **WHEN** the `createsuperuser` job is executed via `gcloud run jobs execute` or the GCP Console
- **THEN** the job completes successfully and a new Django superuser record exists in the database with the configured username, email, and password

#### Scenario: Duplicate username execution
- **WHEN** the `createsuperuser` job is executed and a user with that username already exists in the database
- **THEN** the command exits with standard Django `CommandError: Error: That username is already taken.`
