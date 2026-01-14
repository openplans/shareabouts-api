resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.service_name}-${var.environment}-db-password"
  replication {
    auto {}
  }
}

resource "random_password" "db_password" {
  length  = 16
  special = false
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
