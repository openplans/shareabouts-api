variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "service_name" {
  description = "Name of the service"
  type        = string
  default     = "shareabouts-api"
}

# Inputs from Common Module
variable "vpc_connector_id" {
  description = "ID of the VPC Access Connector"
  type        = string
}

variable "db_instance_name" {
  description = "Name of the shared Cloud SQL Instance"
  type        = string
}

variable "db_private_ip" {
  description = "Private IP of the shared Cloud SQL Instance"
  type        = string
}

variable "redis_host" {
  description = "Host of the shared Redis Instance"
  type        = string
}

variable "redis_port" {
  description = "Port of the shared Redis Instance"
  type        = string
}

# Configuration
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
