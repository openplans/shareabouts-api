resource "google_cloud_run_v2_job" "migrate" {
  name     = "${var.service_name}-${var.environment}-migrate"
  location = var.region

  template {
    template {
      service_account = google_service_account.sa.email
      vpc_access {
        connector = var.vpc_connector_id
        egress    = "ALL_TRAFFIC"
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
