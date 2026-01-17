resource "google_cloud_run_v2_service" "default" {
  name     = "${var.service_name}-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa.email
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = "gcr.io/${var.project_id}/${var.service_name}:latest-${var.environment}" # Assumes image is pushed

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }


      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "DATABASE_HOST"
        value = google_sql_database_instance.instance.private_ip_address
      }
      env {
        name  = "DATABASE_NAME"
        value = google_sql_database.database.name
      }
      env {
        name  = "DATABASE_USER"
        value = google_sql_user.user.name
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
      }
      env {
        name  = "REDIS_KEY_PREFIX"
        value = var.environment
      }
      env {
        name  = "GS_BUCKET_NAME"
        value = google_storage_bucket.static.name
      }
      env {
        name  = "GS_PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "DEBUG"
        value = "False"
      }
      env {
        name  = "ALLOWED_HOSTS"
        value = join(",", concat(["${var.service_name}-${var.environment}-${var.project_id}-${var.region}.run.app"], var.allowed_hosts))
      }
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_v2_service.default.name
  location = google_cloud_run_v2_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
