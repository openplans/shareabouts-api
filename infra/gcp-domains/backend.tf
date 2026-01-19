# ------------------------------------------------------------------------------
# Serverless Network Endpoint Groups (NEGs)
# One per service in domain_mappings
# ------------------------------------------------------------------------------
resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  for_each = var.domain_mappings

  name                  = "${each.key}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = each.value.cloud_run_service.region

  cloud_run {
    service = each.value.cloud_run_service.name
  }
}

# ------------------------------------------------------------------------------
# Backend Services
# One per service in domain_mappings
# ------------------------------------------------------------------------------
resource "google_compute_backend_service" "default" {
  for_each = var.domain_mappings

  name                  = "${each.key}-backend"
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.serverless_neg[each.key].id
  }

  log_config {
    enable = true
  }
}
