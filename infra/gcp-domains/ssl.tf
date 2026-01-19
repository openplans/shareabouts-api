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

  # Domains that fall into the default certificate
  default_domains = setsubtract(local.all_domains, local.explicit_domains)

  # Final map of certificate names to domain lists
  # Only include "default" if there are remaining domains
  certificate_map = merge(
    var.ssl_certs,
    length(local.default_domains) > 0 ? { "default" = tolist(local.default_domains) } : {}
  )
}

# ------------------------------------------------------------------------------
# Managed SSL Certificate
# Creates certificates for each group of domains
# ------------------------------------------------------------------------------
resource "random_id" "certificate" {
  for_each = local.certificate_map

  byte_length = 4
  keepers = {
    domains = join(",", sort(each.value))
  }
}

resource "google_compute_managed_ssl_certificate" "default" {
  for_each = local.certificate_map

  name = "${var.load_balancer_name}-${each.key}-cert-${random_id.certificate[each.key].hex}"

  lifecycle {
    create_before_destroy = true
  }

  managed {
    domains = each.value
  }
}
