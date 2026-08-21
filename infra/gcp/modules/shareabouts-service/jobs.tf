resource "google_cloud_run_v2_job" "migrate" {
  name     = "${var.service_name}-${var.environment}-migrate"
  location = var.region

  template {
    template {
      service_account = google_service_account.sa.email
      vpc_access {
        connector = var.vpc_connector_id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image = "gcr.io/${var.project_id}/${var.service_name}:latest-${var.environment}"

        command = ["python", "manage.py", "migrate"]

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
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
}

resource "google_cloud_run_v2_job" "createsuperuser" {
  count    = local.enable_createsuperuser ? 1 : 0
  name     = "${var.service_name}-${var.environment}-createsuperuser"
  location = var.region

  template {
    template {
      service_account = google_service_account.sa.email
      vpc_access {
        connector = var.vpc_connector_id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image = "gcr.io/${var.project_id}/${var.service_name}:latest-${var.environment}"

        command = ["python", "manage.py", "createsuperuser", "--noinput"]

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
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
          for_each = merge(local.env_secrets, local.superuser_env_secrets)
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
}

