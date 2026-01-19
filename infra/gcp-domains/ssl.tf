# ------------------------------------------------------------------------------
# Collect all unique domains from the domain_mappings for SSL certificate
# ------------------------------------------------------------------------------
locals {
  all_domains = concat(
    flatten([for mapping in var.domain_mappings : mapping.domains]),
    flatten([for rule in var.legacy_host_rules : rule.hosts])
  )

  # Domains explicitly assigned to custom certificates
  explicit_domains = flatten(values(var.ssl_certs))

  # Domains that behave as individuals (one cert per domain)
  individual_domains = setsubtract(local.all_domains, local.explicit_domains)

  # Final map of certificate names to domain lists
  # 1. Custom groups from var.ssl_certs
  # 2. Individual domains (mapped to a list of just themselves)
  certificate_map = merge(
    var.ssl_certs,
    { for d in local.individual_domains : replace(d, ".", "-") => [d] }
  )

  # Flattened list of all domain->cert mapping entries
  # This creates a list of objects like: { domain = "example.com", cert_key = "example-com" }
  certificate_map_entries = flatten([
    for cert_key, domains in local.certificate_map : [
      for domain in domains : {
        domain   = domain
        cert_key = cert_key
      }
    ]
  ])
}

# ------------------------------------------------------------------------------
# Certificate Map
# ------------------------------------------------------------------------------
resource "google_certificate_manager_certificate_map" "default" {
  name        = "${var.load_balancer_name}-map"
  description = "Certificate map for ${var.load_balancer_name}"
}

# ------------------------------------------------------------------------------
# Certificate Manager Certificates
# ------------------------------------------------------------------------------
resource "google_certificate_manager_certificate" "default" {
  for_each = local.certificate_map

  name        = "${var.load_balancer_name}-${each.key}-cert"
  description = "Managed certificate for group: ${each.key}"
  scope       = "DEFAULT"

  managed {
    domains = each.value
  }

  # Be careful when destroying certificates; some cannot be as
  # easily provisioned as others, especially if you don't control
  # the DNS records for the domains.
  lifecycle {
    prevent_destroy = true
  }
}

# ------------------------------------------------------------------------------
# Certificate Map Entries
# ------------------------------------------------------------------------------
resource "google_certificate_manager_certificate_map_entry" "default" {
  for_each = {
    for entry in local.certificate_map_entries : entry.domain => entry
  }

  name        = "entry-${replace(each.value.domain, ".", "-")}"
  description = "Map entry for ${each.value.domain}"
  map         = google_certificate_manager_certificate_map.default.name

  certificates = [google_certificate_manager_certificate.default[each.value.cert_key].id]
  hostname     = each.value.domain
}
