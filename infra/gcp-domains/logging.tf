# ------------------------------------------------------------------------------
# Cloud Logging Saved Queries for Cloud Armor Blocked Requests
# ------------------------------------------------------------------------------

resource "google_logging_saved_query" "blocked_all" {
  name         = "cloud-armor-blocked-all"
  parent       = "projects/${var.project_id}"
  location     = "global"
  display_name = "Cloud Armor - Blocked Requests (All)"
  description  = "All requests denied and returned 403 Forbidden by Cloud Armor security policies."
  visibility   = "SHARED"

  logging_query {
    filter = <<-EOT
resource.type="http_load_balancer"
log_name="projects/${var.project_id}/logs/requests"
jsonPayload.enforcedSecurityPolicy.outcome="DENY"
EOT
  }
}

resource "google_logging_saved_query" "blocked_referer" {
  name         = "cloud-armor-blocked-referer"
  parent       = "projects/${var.project_id}"
  location     = "global"
  display_name = "Cloud Armor - Blocked API Referer Scrapers"
  description  = "Requests blocked by Cloud Armor for matching self-referencing API scraper referer patterns (priority 910)."
  visibility   = "SHARED"

  logging_query {
    filter = <<-EOT
resource.type="http_load_balancer"
log_name="projects/${var.project_id}/logs/requests"
jsonPayload.enforcedSecurityPolicy.priority=910
EOT
  }
}

resource "google_logging_saved_query" "blocked_php" {
  name         = "cloud-armor-blocked-php"
  parent       = "projects/${var.project_id}"
  location     = "global"
  display_name = "Cloud Armor - Blocked PHP Probes"
  description  = "Requests blocked by Cloud Armor for probing .php endpoints (priority 900)."
  visibility   = "SHARED"

  logging_query {
    filter = <<-EOT
resource.type="http_load_balancer"
log_name="projects/${var.project_id}/logs/requests"
jsonPayload.enforcedSecurityPolicy.priority=900
EOT
  }
}

resource "google_logging_saved_query" "blocked_ip_ranges" {
  name         = "cloud-armor-blocked-ip-ranges"
  parent       = "projects/${var.project_id}"
  location     = "global"
  display_name = "Cloud Armor - Blocked IP Ranges"
  description  = "Requests blocked by Cloud Armor for matching blocked IP CIDR ranges (priority 1000)."
  visibility   = "SHARED"

  logging_query {
    filter = <<-EOT
resource.type="http_load_balancer"
log_name="projects/${var.project_id}/logs/requests"
jsonPayload.enforcedSecurityPolicy.priority=1000
EOT
  }
}
