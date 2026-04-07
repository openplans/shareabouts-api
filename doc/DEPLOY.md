These instructions apply only to the "Shareabouts API" application.
If you are also building and installing the Shareabouts web front-end,
it has its own documentation.

Deploying to Heroku
-------------------

0. Clone the shareabouts-api repository
1. Create a Heroku app
2. Add addons

    "heroku-postgresql:standard-0"
    "rediscloud:500"
    "newrelic"
    "adept-scale"
    "pgbackups:auto-month"

3. Promote the new database
4. Set environment variables

        BUILDPACK_URL:               https://github.com/heroku/heroku-buildpack-multi.git
        DEBUG:                       False
        NEW_RELIC_APP_NAME:          Shareabouts API (Production, Heroku)
        REDIS_URL:                   [Set to REDISCLOUD_URL or OPENREDIS_URL]
        SHAREABOUTS_ADMIN_EMAIL:     admin@example.com
        SHAREABOUTS_AWS_BUCKET:      shareabouts_attachments
        SHAREABOUTS_AWS_KEY:         ABCDEFGHIJKL12MNO3PQ
        SHAREABOUTS_AWS_SECRET:      abcDEfGhi+1JKlMnOPqr2sT34UVWXy+zaBcdEFgH
        SHAREABOUTS_FACEBOOK_KEY:    123456789012345
        SHAREABOUTS_FACEBOOK_SECRET: a1234bc56d78ef901g234h567ijklmn8
        SHAREABOUTS_TWITTER_KEY:     aB1cd2EFGhi3JK4lMn5oP
        SHAREABOUTS_TWITTER_SECRET:  ABcDE1FgHIjKlmN2o3pQrsTUVW4X5Cy67zabCdEFGHi
        WORKERS: 4
        BUILD_WITH_GEO_LIBRARIES: 1

5. Connect the app with the repository (add a git remote)
6. Push to Heroku
7. Run database migrations (or copy the database from elsewhere)

Deploying to Google Cloud Platform
----------------------------------

The GCP deployment uses OpenTofu (or Terraform) for infrastructure, Podman for
containerization, and Google Cloud Storage for media assets.

### 1. Prerequisites

- [OpenTofu](https://opentofu.org/) or [Terraform](https://www.terraform.io/)
- [Podman](https://podman.io/) or Docker
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk)

### 2. Infrastructure Setup

Initialize and apply the OpenTofu configuration in the `infra/gcp` directory:

    cd infra/gcp
    tofu init
    tofu apply

This will create the Cloud SQL instance, Cloud Run service, GCS bucket, and other necessary resources.

### 3. Image Deployment

A `Makefile` is provided for common deployment tasks.

1.  **Authenticate with Container Registry** (one-time setup):

    ```bash
    gcloud auth configure-docker gcr.io
    ```

    *(For Podman, you may also need to run:)*

    ```bash
    gcloud auth print-access-token | podman login -u oauth2accesstoken --password-stdin https://gcr.io
    ```

2.  **Set Environment Variables**:

    ```bash
    export PROJECT_ID=your-project-id
    export SERVICE_NAME=your-service-name
    export ENVIRONMENT_NAME=your-environment-name
    export REGION=your-region
    ```

3.  **Deploy** (build, push, and restart Cloud Run):

    ```bash
    make gcp-deploy
    ```

    Or run individual steps:

    ```bash
    make build       # Build the container image locally
    make gcp-push    # Push image to GCR
    make gcp-restart # Update the Cloud Run service
    ```

### 4. Static Files

Currently, static files are served directly by the container using `dj_static.Cling`. Ensure `STATIC_URL` and `STATICFILES_STORAGE` in `settings.py` are configured appropriately (local serving is the default if GCS static configuration is commented out).
