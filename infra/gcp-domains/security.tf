# ------------------------------------------------------------------------------
# Cloud Armor Security Policy
# Blocks traffic from specified IP CIDR ranges and malicious patterns at the Load Balancer level
# ------------------------------------------------------------------------------

locals {
  has_security_rules = (
    length(var.blocked_ip_ranges) > 0 ||
    var.block_php_requests ||
    length(var.blocked_referer_domains) > 0
  )

  # Match only bare-origin referers (no path) — this is the botnet's signature.
  # Exempt requests carrying a Django session cookie so authenticated staff can
  # browse /api/ from the admin or directly in the browser.
  # Uses regex matching to stay within Cloud Armor's 10-expression limit.
  referer_match_expression = length(var.blocked_referer_domains) > 0 ? format(
    "request.path.startsWith('/api/') && has(request.headers['referer']) && (!has(request.headers['cookie']) || !request.headers['cookie'].contains('sessionid=')) && (%s)",
    join(" || ", [
      for d in var.blocked_referer_domains :
      "request.headers['referer'].matches('https?://${replace(d, ".", "\\\\.")}/?')"
    ])
  ) : ""
}

resource "google_compute_security_policy" "ip_blocklist" {
  count       = local.has_security_rules ? 1 : 0
  name        = "${var.load_balancer_name}-ip-blocklist"
  description = "Cloud Armor security policy to block abusive IP ranges and malicious request patterns"

  dynamic "rule" {
    for_each = var.block_php_requests ? [1] : []
    content {
      action   = "deny(403)"
      priority = "900"
      match {
        expr {
          expression = "request.path.endsWith('.php')"
        }
      }
      description = "Deny requests for PHP resources"
    }
  }

  dynamic "rule" {
    for_each = length(var.blocked_referer_domains) > 0 ? [1] : []
    content {
      action   = "deny(403)"
      priority = "910"
      match {
        expr {
          expression = local.referer_match_expression
        }
      }
      description = "Deny requests to /api/ with self-referencing root referer"
    }
  }

  dynamic "rule" {
    for_each = length(var.blocked_ip_ranges) > 0 ? [1] : []
    content {
      action   = "deny(403)"
      priority = "1000"
      match {
        versioned_expr = "SRC_IPS_V1"
        config {
          src_ip_ranges = var.blocked_ip_ranges
        }
      }
      description = "Deny access to specified IP ranges"
    }
  }

  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default rule, allow all traffic"
  }
}

