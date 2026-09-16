## Why

Client frontend domains (such as participate.boston.gov, pbideas.cambridgema.gov, pbsomervillema.poepublic.com, suggest.bluebikes.com) act as public entrypoints for civic engagement maps and surveys. While backend API endpoints handle rate limiting for anonymous API requests at the Django level (`AnonymousIPThrottle`), client frontend domains lack load-balancer level protection against aggressive web scraping, DoS spikes, or abusive crawlers. Implementing per-client IP rate limiting at the Cloud Armor layer protects frontend instances from resource exhaustion without throttling the backend API when legitimate client proxy traffic is routed to it.

## What Changes

- Add configurable IP-based rate limiting rules to Cloud Armor security policies for client frontend domains.
- Parameterize rate limit thresholds (e.g., 100 requests per minute per source IP) and enable/disable toggles via OpenTofu variables.
- Configure rate limit actions to return HTTP 429 Too Many Requests when a client IP exceeds the configured threshold.
- Keep the API server domains exempt from frontend load-balancer rate limits so backend Django-level rate limiting (`AnonymousIPThrottle`) continues to manage API throttling independently.

## Capabilities

### New Capabilities
- `client-domain-rate-limiting`: Configures Cloud Armor IP-based rate limiting on client frontend domains (e.g., 100 requests/minute per client IP) returning HTTP 429 upon exceeding threshold.

### Modified Capabilities
<!-- None -->

## Impact

- **Infrastructure**: `infra/gcp-domains/` (Terraform/OpenTofu definitions for security policies and variables).
- **Security Policy**: Cloud Armor rules updated to include `rate_limit_options` matching client domains.
- **Client Traffic**: End-users accessing client frontends exceeding 100 req/min will receive HTTP 429 responses; normal users and backend API consumers will be unaffected.
