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

      # env {
      #   name = "DATABASE_URL"
      #   value_source {
      #     secret_key_ref {
      #       secret  = google_secret_manager_secret.db_password.secret_id
      #       version = "latest"
      #     }
      #   }
      # }
      # We need to construct the full DB URL.
      # Since we can't easily interpolate secrets into env vars directly in Cloud Run (it supports full value from secret),
      # we might need to change how the app reads DB config OR use a startup script.
      # HOWEVER, Cloud Run supports mounting secrets as files or env vars.
      # Let's use the env var approach but we need to construct the connection string.
      # DJANGO_DATABASE_URL expects the full string.
      # Alternative: Pass DB_PASSWORD as a separate env var and construct DATABASE_URL in settings.py or entrypoint.
      # Let's assume we can change settings.py or use a script.
      # For now, let's pass DB_PASSWORD as an env var.

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
        value = "*" # Should be restricted in production
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
