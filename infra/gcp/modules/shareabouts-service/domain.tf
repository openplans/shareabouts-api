# ------------------------------------------------------------------------------
# Domain Mapping
# ------------------------------------------------------------------------------
#
# Domain mapping for this Cloud Run service is managed in a separate project.
#
# WHY A SEPARATE PROJECT?
# -----------------------
# The `google_cloud_run_domain_mapping` resource is designed for the Cloud Run
# v1 API, but this service uses `google_cloud_run_v2_service`. While v1 domain
# mapping may technically work, it's not officially recommended for v2 services
# and may have compatibility issues or limited feature support.
#
# The recommended approach for v2 is to use a Global External Application Load
# Balancer with:
#   - Serverless NEG (Network Endpoint Group)
#   - Backend Service
#   - URL Map with host rules
#   - Managed SSL certificates
#
# Since we share a load balancer across multiple services, this configuration
# lives in the central `gcp-domains` project to avoid Terraform state conflicts.
#
# FUTURE CONSIDERATIONS
# ---------------------
# If Google introduces a v2-compatible domain mapping resource (e.g.,
# `google_cloud_run_v2_domain_mapping`), it would be simpler to manage domain
# configuration directly in this project alongside the Cloud Run service.
# Monitor the Terraform Google provider changelog for updates.
#
# TO CONFIGURE DOMAINS
# --------------------
# 1. Deploy this service: `tofu apply`
# 2. Add an entry to `../gcp-domains/.auto.tfvars`:
#
#    domain_mappings = {
#      shareabouts-api-dev = {
#        domains = ["shareaboutsapi-gcp-dev.poepublic.com"]
#        cloud_run_service = {
#          name   = "shareabouts-api-dev"  # Use output: cloud_run_service_name
#          region = "us-central1"
#        }
#      }
#    }
#
# 3. Apply the domain mapping: `cd ../gcp-domains && tofu apply`
# ------------------------------------------------------------------------------
