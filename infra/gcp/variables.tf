variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The environment"
  type        = string
}

variable "service_name" {
  description = "The Cloud Run service name"
  type        = string
  default     = "shareabouts-api"
}

variable "domain_names" {
  description = "Custom domain names for ALLOWED_HOSTS configuration"
  type        = list(string)
  default     = []
}

variable "additional_allowed_hosts" {
  description = "Additional allowed hosts; ALLOWED_HOSTS will always include the Cloud Run service URL and the provided domain names. Set to [] to only allow those two. Set to [\"*\"] to allow all hosts (not recommended for production)."
  type        = list(string)
  default     = []
}
