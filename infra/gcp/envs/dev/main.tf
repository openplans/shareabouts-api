terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }

  backend "gcs" {
    bucket = "${var.project_id}-tfstate"
    prefix = "api/dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ------------------------------------------------------------------------------
# REMOTE STATE (COMMON)
# ------------------------------------------------------------------------------

data "terraform_remote_state" "common" {
  backend = "gcs"

  config = {
    bucket = "${var.project_id}-tfstate"
    prefix = "api/common"
  }
}

# ------------------------------------------------------------------------------
# SERVICE MODULE
# ------------------------------------------------------------------------------

module "service" {
  source = "../../modules/shareabouts-service"

  project_id   = var.project_id
  region       = var.region
  service_name = var.service_name
  environment  = "dev"

  # Inputs from Common
  vpc_connector_id = data.terraform_remote_state.common.outputs.vpc_connector_id
  db_instance_name = data.terraform_remote_state.common.outputs.db_instance_name
  db_private_ip    = data.terraform_remote_state.common.outputs.db_private_ip
  redis_host       = data.terraform_remote_state.common.outputs.redis_host
  redis_port       = data.terraform_remote_state.common.outputs.redis_port

  # Config
  domain_names             = var.domain_names
  additional_allowed_hosts = var.additional_allowed_hosts
}
