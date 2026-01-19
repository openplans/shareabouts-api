resource "google_secret_manager_secret" "tfvars" {
  secret_id = "${var.load_balancer_name}-tfvars"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "tfvars" {
  secret = google_secret_manager_secret.tfvars.id

  secret_data = <<EOT
load_balancer_name      = "${var.load_balancer_name}"
default_backend_service = ${var.default_backend_service == null ? "null" : "\"${var.default_backend_service}\""}
default_redirect_host   = "${var.default_redirect_host}"

domain_mappings = ${jsonencode(var.domain_mappings)}

legacy_host_rules = ${jsonencode(var.legacy_host_rules)}

ssl_certs = ${jsonencode(var.ssl_certs)}
EOT
}
