terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }

  backend "gcs" {
    bucket = "${var.project_id}-tfstate"
    prefix = "api/common"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "common" {
  source = "../../modules/common"

  project_id   = var.project_id
  region       = var.region
  service_name = var.service_name
}

output "vpc_connector_id" {
  value = module.common.vpc_connector_id
}

output "db_instance_name" {
  value = module.common.db_instance_name
}

output "db_private_ip" {
  value = module.common.db_private_ip
}

output "redis_host" {
  value = module.common.redis_host
}

output "redis_port" {
  value = module.common.redis_port
}
