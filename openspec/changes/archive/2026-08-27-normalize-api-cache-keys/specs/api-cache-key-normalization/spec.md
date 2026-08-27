## Purpose

Canonicalizes and normalizes Redis cache keys across response format, query parameter ordering, and composite authorization scopes to eliminate cache fragmentation and guarantee secure cache isolation.

## ADDED Requirements

### Requirement: Format Normalization in Cache Keys
The API cache system SHALL key cached responses on the normalized response format (e.g., `json`, `api`, `geojson`) rather than raw client `HTTP_ACCEPT` header strings.

#### Scenario: Diverse clients requesting identical format
- **WHEN** multiple HTTP clients send requests to the same URL with different `Accept` headers but resolve to the same response format (e.g., `json`)
- **THEN** all requests produce the same format component in the cache key and share the cached response

### Requirement: Query Parameter Canonicalization
The API cache system SHALL canonicalize query strings by sorting key-value parameters alphabetically and removing jQuery-style cache busting parameters (`_=\d+`).

#### Scenario: Differently ordered query parameters
- **WHEN** requests arrive with the same query parameters in different order (e.g., `?page=2&include_submissions=true` and `?include_submissions=true&page=2`)
- **THEN** both requests produce the exact same canonicalized query string component in the cache key

### Requirement: Composite User and Client Authorization Scope
The API cache system SHALL scope cached responses by both user authorization status (anonymous, superuser, owner, or group list) and client identity (API key or CORS origin).

#### Scenario: Anonymous public traffic sharing cache
- **WHEN** unauthenticated requests arrive without API keys or custom CORS origin policies
- **THEN** the auth scope evaluates to a shared anonymous public scope (`anon;client:none`), allowing all public visitors and web crawlers to share the cached response

#### Scenario: API key credential isolation
- **WHEN** an authenticated request arrives with a valid API key
- **THEN** the cache key incorporates the API key identifier, ensuring responses with privileged access permissions are isolated from public anonymous cache entries

#### Scenario: CORS origin credential isolation
- **WHEN** an authenticated request arrives with a recognized CORS origin pattern
- **THEN** the cache key incorporates the origin identifier, isolating origin-scoped permissions

### Requirement: Semicolon Delimited Cache Key Structure
The API cache system SHALL join top-level cache key components using semicolons (`;`) as delimiters.

#### Scenario: Cache key serialization format
- **WHEN** a cache key is generated for an endpoint
- **THEN** the key string is constructed as `<path>;<format>;<sorted_query>;<user_scope>;<client_scope>`
