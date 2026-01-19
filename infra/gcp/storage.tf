resource "google_storage_bucket" "static" {
  name          = "${var.service_name}-${var.environment}-static-${var.project_id}" # Must be globally unique
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
