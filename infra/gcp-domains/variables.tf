variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The default GCP region"
  type        = string
  default     = "us-central1"
}

variable "load_balancer_name" {
  description = "The name of the load balancer (URL map name)"
  type        = string
}

variable "domain_mappings" {
  description = "Map of service names to their domain and Cloud Run service configurations"
  type = map(object({
    domains = list(string)
    cloud_run_service = object({
      name   = string
      region = string
    })
  }))
  default = {}
}

variable "legacy_host_rules" {
  description = "Existing host rules to preserve (for backend services not managed by this project)"
  type = map(object({
    hosts           = list(string)
    path_matcher    = string
    backend_service = string # Full backend service URL
  }))
  default = {}
}

variable "default_backend_service" {
  description = "The default backend service for unmatched requests (optional, if not set uses redirect)"
  type        = string
  default     = null
}

variable "default_redirect_host" {
  description = "The host to redirect unmatched requests to (used when default_backend_service is null)"
  type        = string
  default     = "poepublic.com"
}

variable "ssl_certs" {
  type        = map(list(string))
  description = "A map of custom SSL certificate groups. Any domains not in this map will be grouped into a default certificate."
  default     = {}
}
