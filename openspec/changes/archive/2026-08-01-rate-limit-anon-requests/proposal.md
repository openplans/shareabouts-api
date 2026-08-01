## Why

Currently, there is no rate limiting on the Shareabouts API, making it vulnerable to abuse from unauthenticated clients. We need to throttle fully anonymous requests (those without a logged-in user, an API key, or a registered CORS origin) by their IP address to protect system resources.

## What Changes

- Add a custom DRF throttle class (`AnonymousIPThrottle`) that only applies to fully anonymous requests. Client-authenticated requests (API key/CORS origin) and user-authenticated requests will bypass this throttle.
- Apply this throttle class globally to all DRF API views via `DEFAULT_THROTTLE_CLASSES`.
- Make the throttle rate environment-configurable via `ANON_THROTTLE_RATE`, defaulting to `20/min`.
- Make the number of proxies environment-configurable via `NUM_PROXIES` (defaulting to `None`) so that DRF can correctly extract the client IP from the `X-Forwarded-For` header without exposing the system to spoofing attacks when proxies are involved.

## Capabilities

### New Capabilities

- `rate-limit-anon`: Throttling of fully anonymous requests by IP address.

### Modified Capabilities

None.

## Impact

- `src/sa_api_v2/throttling.py`: New module containing the custom throttle class.
- `src/project/settings.py`: Updated to configure DRF throttling (`DEFAULT_THROTTLE_CLASSES`, `DEFAULT_THROTTLE_RATES`, and `NUM_PROXIES`).
- All API endpoints will automatically enforce the new anonymous rate limit. Non-API routes (like the Django admin) will not be affected.
