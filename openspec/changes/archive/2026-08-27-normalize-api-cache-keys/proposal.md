## Why

`CachedResourceMixin` currently generates Redis cache keys using the client's raw `HTTP_ACCEPT` header string, un-sorted raw query string, and only user-level groups. Different browsers, search spiders, and frontend fetch clients send distinct `Accept` headers, causing complete cache fragmentation and forcing the API to repeatedly run 1–2 second database queries and Python GeoJSON serializations for identical public datasets. Additionally, client credentials (API keys and CORS origins) are omitted from the cache key, risking cross-client data leakage.

## What Changes

- Replace the raw `HTTP_ACCEPT` header with the normalized response format (e.g., `json`, `api`, `geojson`) in cache keys.
- Canonicalize query strings by sorting query parameters alphabetically to eliminate ordering-based cache misses.
- Expand the cache key authorization scope into a composite identifier that incorporates both user identity (`anon`, `superuser`, `owner`, or dataset groups) and client credentials (`client:none`, `apikey:<key>`, or `origin:<pattern>`).
- Use semicolons (`;`) as the delimiter separating top-level cache key components.

## Capabilities

### New Capabilities
- `api-cache-key-normalization`: Canonicalizes API cache keys in `CachedResourceMixin` using normalized response format, sorted query strings, composite user/client auth scopes, and semicolon delimiters.

### Modified Capabilities
<!-- None -->

## Impact

- **Views**: `src/sa_api_v2/views/base_views.py` (`CachedResourceMixin.get_cache_key`).
- **Tests**: Updates and additions to `src/sa_api_v2/tests/test_views.py` and caching tests.
- **Performance**: High cache hit rates across web crawlers and frontend clients for public dataset endpoints.
