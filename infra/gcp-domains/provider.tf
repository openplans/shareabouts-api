terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "gcs" {
    bucket = "${var.project_id}-tfstate"
    prefix = "domains"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
