terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}

data "google_project" "project" {
}

locals {
  default_cloud_run_domain = "${var.service_name}-${var.environment}-${data.google_project.project.number}.${var.region}.run.app"

  env_vars = {
    "DATABASE_HOST"           = var.db_private_ip
    "DATABASE_NAME"           = google_sql_database.database.name
    "DATABASE_USER"           = google_sql_user.user.name
    "REDIS_URL"               = "redis://${var.redis_host}:${var.redis_port}/0"
    "REDIS_KEY_PREFIX"        = var.environment
    "GS_BUCKET_NAME"          = google_storage_bucket.static.name
    "GS_PROJECT_ID"           = var.project_id
    "DEBUG"                   = "False"
    "WORKERS"                 = var.workers
    "SHAREABOUTS_ADMIN_EMAIL" = var.shareabouts_admin_email
    "ALLOWED_HOSTS" = join(",", concat(
      [local.default_cloud_run_domain],
      var.domain_names,
      var.additional_allowed_hosts
    ))
  }

  env_secrets = {
    "DB_PASSWORD" = google_secret_manager_secret.db_password.secret_id
    "SECRET_KEY"  = google_secret_manager_secret.secret_key.secret_id
  }
}

# ------------------------------------------------------------------------------
# DATABASE & USERS
# ------------------------------------------------------------------------------

resource "random_password" "db_password" {
  length  = 16
  special = false
}

resource "google_sql_database" "database" {
  name     = "${var.service_name}-${var.environment}"
  instance = var.db_instance_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_sql_user" "user" {
  name     = "${var.service_name}-${var.environment}"
  instance = var.db_instance_name
  password = random_password.db_password.result
}

# ------------------------------------------------------------------------------
# STORAGE
# ------------------------------------------------------------------------------

resource "google_storage_bucket" "static" {
  name                        = "${var.service_name}-${var.environment}-static-${var.project_id}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# ------------------------------------------------------------------------------
# SECRETS
# ------------------------------------------------------------------------------

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.service_name}-${var.environment}-db-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "${var.service_name}-${var.environment}-secret-key"
  replication {
    auto {}
  }
}

resource "random_password" "secret_key" {
  length  = 50
  special = true
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = random_password.secret_key.result
}

resource "google_secret_manager_secret" "tfvars" {
  secret_id = "${var.service_name}-${var.environment}-tfvars"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "tfvars" {
  secret      = google_secret_manager_secret.tfvars.id
  secret_data = <<EOT
service_name             = "${var.service_name}"
environment              = "${var.environment}"
region                   = "${var.region}"

domain_names             = ${jsonencode(var.domain_names)}
additional_allowed_hosts = ${jsonencode(var.additional_allowed_hosts)}
workers                  = "${var.workers}"
EOT
}

# ------------------------------------------------------------------------------
# SERVICE ACCOUNT & IAM
# ------------------------------------------------------------------------------

resource "google_service_account" "sa" {
  account_id   = "${var.service_name}-${var.environment}-sa"
  display_name = "Cloud Run Service Account"
}

resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.sa.email}"
}

resource "google_storage_bucket_iam_member" "storage_admin" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.sa.email}"
}

resource "google_secret_manager_secret_iam_member" "db_password_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_key_access" {
  secret_id = google_secret_manager_secret.secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sa.email}"
}

# ------------------------------------------------------------------------------
# CLOUD RUN
# ------------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "default" {
  name                = "${var.service_name}-${var.environment}"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  scaling {
    min_instance_count = var.min_instances
    max_instance_count = var.max_instances
  }

  template {
    service_account = google_service_account.sa.email
    vpc_access {
      connector = var.vpc_connector_id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = "gcr.io/${var.project_id}/${var.service_name}:latest-${var.environment}"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }

      dynamic "env" {
        for_each = local.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.env_secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_v2_service.default.name
  location = google_cloud_run_v2_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
