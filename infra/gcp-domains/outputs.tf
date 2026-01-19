output "load_balancer_ip" {
  description = "The IP address of the load balancer"
  value       = google_compute_global_forwarding_rule.default.ip_address
}

output "ssl_certificate_domains" {
  description = "The domains covered by the Certificate Manager certificates"
  value = {
    for k, v in google_certificate_manager_certificate.default : k => v.managed[0].domains
  }
}

output "configured_services" {
  description = "The services configured in the URL map"
  value       = keys(var.domain_mappings)
}
