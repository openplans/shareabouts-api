## Context

The API currently performs authentication for both users (session/basic) and clients (API keys/CORS origins). However, it completely lacks rate limiting for requests that provide neither. Since the API sits behind a reverse proxy, the client IP is located in the `X-Forwarded-For` header.

## Goals / Non-Goals

**Goals:**
- Rate limit unauthenticated, keyless requests based on their true IP address.
- Provide a mechanism to safely extract the client IP when operating behind reverse proxies.
- Allow simple configuration of rate limits via environment variables.

**Non-Goals:**
- Rate limiting for authenticated users or API key clients (they manage their own downstream limits).
- Complex rate limiting rules (e.g., dynamic limits based on paths).

## Decisions

- **DRF Built-in Throttling**: We will use Django REST Framework's `SimpleRateThrottle`.
  - *Rationale*: DRF's built-in throttling integrates naturally with our DRF-based API, handles the HTTP 429 logic, and uses Django's cache framework out of the box (which is already configured to use Redis in production).
  - *Alternatives*: Writing custom middleware. Middleware would be harder to integrate with DRF's authentication classes, meaning we'd have to replicate auth-checking logic to bypass the throttle for authenticated users.

- **Custom Throttle Class (`AnonymousIPThrottle`)**:
  - *Rationale*: DRF's `AnonRateThrottle` only checks `request.user.is_authenticated`. In our system, an "anonymous" request is one with NO user AND NO `request.client` (API key/origin). A custom subclass allows us to check both before applying the throttle.

- **Global Configuration**:
  - *Rationale*: We will configure the throttle in `REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES']` so that it applies to all DRF API views by default. This ensures no new DRF endpoints accidentally leak unthrottled access. Non-DRF routes (like Django admin) remain unaffected.

- **Proxy Configuration via `NUM_PROXIES`**:
  - *Rationale*: To correctly identify IP addresses behind a proxy using `X-Forwarded-For`, we must configure DRF's `NUM_PROXIES` setting. If left unset, DRF uses the entire header string, which is vulnerable to spoofing. We will expose `NUM_PROXIES` as an environment variable (defaulting to `None` for backward compatibility when running locally without a proxy, though it should be set to `1` or higher in proxy environments).

## Risks / Trade-offs

- [Risk] Spoofing bypass if `NUM_PROXIES` is not configured correctly in a proxied environment.
  - *Mitigation*: Clearly document that `NUM_PROXIES` must be set in production, matching the actual reverse proxy depth.
