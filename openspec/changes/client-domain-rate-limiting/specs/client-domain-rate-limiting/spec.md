## Purpose

Enforces IP-based rate limiting on client frontend domains via Cloud Armor to protect frontend services from abusive traffic and scraping spikes while exempting backend API services.

## ADDED Requirements

### Requirement: Cloud Armor Rate Limiting on Client Frontend Domains
The load balancer security policy SHALL enforce IP-based rate limiting on HTTP requests targeting client frontend domains, throttling requests that exceed a configurable rate threshold with an HTTP 429 Too Many Requests response.

#### Scenario: Client IP within threshold
- **WHEN** an HTTP request is made to a client frontend domain (e.g., `participate.boston.gov`, `pbideas.cambridgema.gov`) from an IP that has made fewer than the allowed number of requests within the rate limit window
- **THEN** the request is allowed to proceed to the frontend service backend

#### Scenario: Client IP exceeds threshold
- **WHEN** an HTTP request is made to a client frontend domain from an IP that exceeds the configured request rate (e.g., more than 100 requests in a 60-second window)
- **THEN** the load balancer responds immediately with HTTP status 429 Too Many Requests and blocks further requests from that IP for the remainder of the interval

### Requirement: Backend API Services Exempt from Frontend Rate Limits
The load balancer security policy SHALL NOT enforce the frontend IP rate limiting rule on API backend domains, allowing backend Django-level rate limiting (`AnonymousIPThrottle`) to independently manage API throttling.

#### Scenario: Direct request or proxied client request to API domain
- **WHEN** an HTTP request is made to an API server domain (e.g., `shareaboutsapi.poepublic.com` or `shareaboutsapi-gcp-prod.poepublic.com`)
- **THEN** the Cloud Armor client-domain rate limit rule is bypassed and does not throttle the request

### Requirement: Configurable Rate Limit Parameters
The infrastructure configuration SHALL expose variables for the rate limit threshold (request count), rate limit window (interval in seconds), and a toggle to enable or disable client-domain rate limiting.

#### Scenario: Customizing rate limit thresholds via variables
- **WHEN** the rate limit count, interval, or enabled flag is modified in Terraform/OpenTofu variable files
- **THEN** Cloud Armor security policy rate limit rules dynamically update to match the configured values without altering unaffected security rules
