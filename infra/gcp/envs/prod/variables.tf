variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region (e.g. us-central1)"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the service (used for naming resources)"
  type        = string
  default     = "shareabouts-api"
}

variable "domain_names" {
  description = "List of custom domain names to map to the service"
  type        = list(string)
  default     = []
}

variable "additional_allowed_hosts" {
  description = "List of additional hosts to allow in Django"
  type        = list(string)
  default     = []
}
