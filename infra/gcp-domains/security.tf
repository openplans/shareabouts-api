# ------------------------------------------------------------------------------
# Cloud Armor Security Policy
# Blocks traffic from specified IP CIDR ranges at the Load Balancer level
# ------------------------------------------------------------------------------

resource "google_compute_security_policy" "ip_blocklist" {
  count       = length(var.blocked_ip_ranges) > 0 ? 1 : 0
  name        = "${var.load_balancer_name}-ip-blocklist"
  description = "Cloud Armor security policy to block abusive IP ranges"

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
