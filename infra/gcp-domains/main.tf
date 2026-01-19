# ------------------------------------------------------------------------------
# URL Map
# This resource should be IMPORTED from the existing load balancer.
# Run: tofu import google_compute_url_map.default projects/PROJECT_ID/global/urlMaps/LOAD_BALANCER_NAME
#
# NOTE: Existing host rules from the imported URL map that are not in
# domain_mappings will be removed. To preserve them, add them to domain_mappings
# or use legacy_host_rules variable.
# ------------------------------------------------------------------------------
resource "google_compute_url_map" "default" {
  name = var.load_balancer_name

  # Default: redirect unmatched hosts to a specified URL, or return 404
  dynamic "default_url_redirect" {
    for_each = var.default_backend_service == null ? [1] : []
    content {
      https_redirect         = true
      redirect_response_code = "FOUND"
      strip_query            = false
      host_redirect          = var.default_redirect_host
    }
  }

  # If a default backend service is specified, use it instead of redirect
  default_service = var.default_backend_service

  # Legacy host rules (for existing mappings not managed by this project)
  dynamic "host_rule" {
    for_each = var.legacy_host_rules
    content {
      hosts        = host_rule.value.hosts
      path_matcher = host_rule.value.path_matcher
    }
  }

  # Dynamic host rules for each service in domain_mappings
  dynamic "host_rule" {
    for_each = var.domain_mappings
    content {
      hosts        = host_rule.value.domains
      path_matcher = host_rule.key
    }
  }

  # Path matchers for legacy host rules (uses existing backend services)
  dynamic "path_matcher" {
    for_each = var.legacy_host_rules
    content {
      name            = path_matcher.value.path_matcher
      default_service = path_matcher.value.backend_service
    }
  }

  # Path matchers for domain_mappings (uses our created backend services)
  dynamic "path_matcher" {
    for_each = var.domain_mappings
    content {
      name            = path_matcher.key
      default_service = google_compute_backend_service.default[path_matcher.key].id
    }
  }
}

# ------------------------------------------------------------------------------
# Target HTTPS Proxy
# This resource should be IMPORTED from the existing load balancer.
# Run: tofu import google_compute_target_https_proxy.default projects/PROJECT_ID/global/targetHttpsProxies/PROXY_NAME
# ------------------------------------------------------------------------------
resource "google_compute_target_https_proxy" "default" {
  name            = "${var.load_balancer_name}-proxy"
  url_map         = google_compute_url_map.default.id
  certificate_map = "//certificatemanager.googleapis.com/${google_certificate_manager_certificate_map.default.id}"
}


# ------------------------------------------------------------------------------
# Global Forwarding Rule
# This resource should be IMPORTED from the existing load balancer.
# Run: tofu import google_compute_global_forwarding_rule.default projects/PROJECT_ID/global/forwardingRules/RULE_NAME
# ------------------------------------------------------------------------------
resource "google_compute_global_forwarding_rule" "default" {
  name                  = "${var.load_balancer_name}-fe"
  target                = google_compute_target_https_proxy.default.id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# ------------------------------------------------------------------------------
# HTTP to HTTPS Redirect
# These resources handle HTTP requests and redirect them to HTTPS
# ------------------------------------------------------------------------------

# URL Map for HTTP redirect (redirects all HTTP to HTTPS)
resource "google_compute_url_map" "http_redirect" {
  name = "${var.load_balancer_name}-http"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

# Target HTTP Proxy
resource "google_compute_target_http_proxy" "default" {
  name    = "${var.load_balancer_name}-proxy-http"
  url_map = google_compute_url_map.http_redirect.id
}

# Global Forwarding Rule for HTTP
resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${var.load_balancer_name}-fe-http"
  target                = google_compute_target_http_proxy.default.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}
