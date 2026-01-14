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

variable "domain_name" {
  description = "The custom domain name"
  type        = string
}
