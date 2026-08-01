## Purpose
Protects the API from abuse by rate-limiting fully anonymous requests by IP address.

## ADDED Requirements

### Requirement: Throttle fully anonymous requests
The system SHALL rate limit requests from fully anonymous clients based on their IP address.

#### Scenario: Anonymous client exceeds rate limit
- **WHEN** an unauthenticated client with no API key and no CORS origin makes requests exceeding the configured limit
- **THEN** the API returns a 429 Too Many Requests response

#### Scenario: Anonymous client stays within rate limit
- **WHEN** an unauthenticated client with no API key and no CORS origin makes requests within the configured limit
- **THEN** the API processes the requests normally

### Requirement: Exempt authenticated users
The system SHALL NOT rate limit requests from users who are logged into the system.

#### Scenario: Logged in user makes many requests
- **WHEN** a user authenticated via session or basic auth makes requests exceeding the anonymous limit
- **THEN** the API processes the requests normally without throttling

### Requirement: Exempt client-authenticated requests
The system SHALL NOT rate limit requests that provide valid client authentication (API key or CORS origin).

#### Scenario: API key client makes many requests
- **WHEN** a client providing a valid API key makes requests exceeding the anonymous limit
- **THEN** the API processes the requests normally without throttling

### Requirement: Respect proxy topology
The system SHALL extract the true client IP from the `X-Forwarded-For` header based on a configured proxy depth, to accurately throttle clients behind proxies and avoid spoofing.

#### Scenario: Request behind a configured number of proxies
- **WHEN** a request arrives with an `X-Forwarded-For` header and the proxy depth is configured to N
- **THEN** the system uses the Nth-from-last IP in the header chain for throttling
