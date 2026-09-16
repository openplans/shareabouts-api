## Why

The Shareabouts API production service is experiencing severe degraded performance and frequent HTTP 429 errors caused by automated scrapers crawling historical, defunct datasets (such as older `ourmiami` and `pbnyc` cycles from 2014–2019). These scraping requests target deep submission and comment endpoints with expensive parameters (`?format=csv` and `?format=jsonp`), causing resource exhaustion on the `db-f1-micro` Cloud SQL database and saturating all Cloud Run container workers.

Because the scraping traffic is distributed across hundreds of unique residential and mobile IPs, application-level rate limiting (`AnonymousIPThrottle`) does not prevent the crawler from overwhelming the system, while causing Cloud Run to abort legitimate traffic when container capacity is exhausted. Blocking these defunct datasets at the Google Cloud Load Balancer (Cloud Armor) level stops the traffic at Google's edge before requests ever wake Cloud Run instances or query Cloud SQL.

## What Changes

- Add a `blocked_datasets` variable to `infra/gcp-domains/variables.tf` as a list of objects containing `owner` and `slug` attributes.
- Update `infra/gcp-domains/security.tf` to generate a Cloud Armor security rule (deny 404 or 403) matching incoming request paths for configured blocked datasets (e.g., `/api/v2/<owner>/datasets/<slug>`).
- Populate `infra/gcp-domains/.auto.tfvars` (and `.auto.tfvars.example`) with the list of defunct dataset pairs identified in production logs (including historical `ourmiami` and `pbnyc` cycles).
- Maintain infrastructure flexibility so datasets can be added, updated, or unblocked via `.auto.tfvars` without modifying core Terraform logic.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `request-filtering`: Adds requirement to block HTTP requests targeting configured defunct dataset paths (`/api/v2/<owner>/datasets/<slug>`) at the Cloud Armor load balancer level.

## Impact

- **Infrastructure**: Updates `infra/gcp-domains/variables.tf`, `security.tf`, and `.auto.tfvars`.
- **Cloud Armor**: Adds a new security rule to the `custom-domains-b84d-ip-blocklist` policy.
- **Service Performance**: Eliminates the vast majority of crawler-induced database load and Cloud Run concurrency saturation, resolving 429 instance aborts for legitimate users.
- **API Clients**: Requests to blocked dataset endpoints will receive an immediate HTTP 404 (or 403) at Google's edge.
