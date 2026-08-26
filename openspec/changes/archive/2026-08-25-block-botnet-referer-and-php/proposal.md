## Why

The Shareabouts API production service is currently experiencing high-volume abusive traffic from a distributed residential proxy botnet and automated vulnerability scanners. Because the botnet rotates across thousands of unique IP addresses, IP-level blocking alone is insufficient. 

To restore service stability and protect backend instances from resource exhaustion, Cloud Armor security policies must be enhanced to block malicious requests based on request signatures (such as hardcoded API referers targeting API endpoints and probes for `.php` resources) while keeping all domain names and patterns configurable to avoid hardcoded domain strings in Terraform code.

## What Changes

- Add configurable Cloud Armor rules to block requests ending in `.php` (vulnerability scanning probes) at the load balancer level.
- Add configurable Cloud Armor rules to block requests to `/api/` endpoints that present suspicious self-referencing referer headers (e.g., `https://<domain>` without subpaths) matching configured API domains.
- Provide Terraform variables and `.auto.tfvars` configuration for blocked referer domains and path patterns, avoiding hardcoded domains in `.tf` infrastructure files.
- Clean up invalid link-local IP (`169.254.169.126/32`) from the IP blocklist.

## Capabilities

### New Capabilities
- `request-filtering`: Configures Cloud Armor security rules to filter and deny malicious HTTP requests by path patterns (such as PHP probes) and suspicious header signatures (such as abusive API referer domains) before reaching backend Cloud Run services.

### Modified Capabilities

## Impact

- **Infrastructure**: Updates `infra/gcp-domains/security.tf`, `variables.tf`, and `.auto.tfvars`.
- **GCP Resources**: Modifies Cloud Armor security policy `custom-domains-b84d-ip-blocklist` attached to backend services.
- **Service Availability**: Stops distributed botnet traffic and PHP exploit scans at Google's edge, preventing Cloud Run instance exhaustion and PostgreSQL connection starvation.
