resource "google_cloud_run_domain_mapping" "default" {
  for_each = toset(var.domain_names)
  location = var.region
  name     = each.value

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.default.name
  }
}
