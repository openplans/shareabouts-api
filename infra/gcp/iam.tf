# Service Account for Cloud Run
resource "google_service_account" "sa" {
  account_id   = "${var.service_name}-${var.environment}-sa"
  display_name = "Cloud Run Service Account"
}

# Grant Cloud Run SA access to Cloud SQL
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.sa.email}"
}

# Grant Cloud Run SA access to GCS
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

