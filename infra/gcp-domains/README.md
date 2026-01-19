# Central Domain Management

This Tofu project manages the shared load balancer and domain mappings for all services.

## Architecture

All domain routing is centralized here because:
- `google_cloud_run_domain_mapping` is designed for Cloud Run v1 API
- Our services use `google_cloud_run_v2_service` (v2 API)
- The recommended v2 approach is a Global External Application Load Balancer

This project dynamically creates:
- Serverless NEGs for each Cloud Run service
- Backend Services for each NEG
- URL Map host rules for domain routing
- Managed SSL certificates

## Setup

1. Copy `.auto.tfvars.example` to `.auto.tfvars` and configure
2. Initialize: `tofu init`
3. Import existing resources (first time only):
   ```bash
   tofu import google_compute_url_map.default projects/poepublic-shareabouts/global/urlMaps/custom-domains-b84d
   tofu import google_compute_target_https_proxy.default projects/poepublic-shareabouts/global/targetHttpsProxies/PROXY_NAME
   tofu import google_compute_global_forwarding_rule.default projects/poepublic-shareabouts/global/forwardingRules/RULE_NAME
   ```
4. Plan and apply: `tofu plan && tofu apply`

## Adding a New Service

1. Deploy your service (e.g., in `../gcp/`)
2. Add an entry to `domain_mappings` in `.auto.tfvars`:
   ```hcl
   domain_mappings = {
     my-service = {
       domains = ["my-domain.example.com"]
       cloud_run_service = {
         name   = "my-service-name"  # From service project output
         region = "us-central1"
       }
     }
   }
   ```
3. Run `tofu apply`

## SSL Certificate Management

To optimize quota usage and avoid re-provisioning all domains when one changes, you can group domains into separate managed SSL certificates using the `ssl_certs` variable.

```hcl
ssl_certs = {
  group-name-1 = ["domain1.com", "domain2.com"]
  group-name-2 = ["domain3.com"]
}
```

- Any domains listed in `ssl_certs` will get their own dedicated certificate.
- Any domains **not** listed in `ssl_certs` (but present in `domain_mappings` or `legacy_host_rules`) will be automatically bundled into a "default" certificate.
- This allows you to isolate high-churn domains or group by organization.

## Future Considerations

If Google introduces a v2-compatible domain mapping resource (e.g., `google_cloud_run_v2_domain_mapping`), consider migrating domain configuration back to individual service projects for simpler management.
