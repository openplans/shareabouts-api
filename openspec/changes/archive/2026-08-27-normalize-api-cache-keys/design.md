## Context

In `src/sa_api_v2/views/base_views.py`, `CachedResourceMixin` provides response caching across all dataset, place, and submission endpoints. The current implementation in `get_cache_key` concatenates the raw `HTTP_ACCEPT` header string, the un-sorted raw query string, and user group names using colons (`:`).

See `proposal.md` for motivation and `specs/api-cache-key-normalization/spec.md` for requirements.

## Goals / Non-Goals

**Goals:**
- Unify cache keys across all HTTP clients requesting identical content types.
- Canonicalize query strings so parameter ordering differences do not cause cache misses.
- Safely isolate cached responses across distinct user and client authorization boundaries.
- Use semicolons (`;`) to separate key components for clean delimiter separation.

**Non-Goals:**
- Changing underlying cache storage backends (Redis remains the cache store).
- Changing dataset model-level invalidation hooks or cache prefixes.

## Decisions

### Decision: Response Format Normalization
- **Choice**: Extract the negotiated format (e.g., `json`, `geojson`, `api`, `csv`) using DRF's format negotiation logic or query parameter `format`, falling back to `json` for standard JSON clients.
- **Rationale**: Replaces hundreds of variations of raw `Accept` headers (Chrome, Firefox, Googlebot, Baiduspider, Axios) with a single normalized token, allowing all JSON consumers to share cache entries.

### Decision: Query String Canonicalization
- **Choice**: Parse the query string into key-value pairs via `urllib.parse.parse_qsl()`, strip jQuery cache-busting keys (`_`), sort tuples alphabetically, and rebuild via `urllib.parse.urlencode()`.
- **Rationale**: Eliminates ordering differences (e.g. `?page=2&include_submissions=true` vs `?include_submissions=true&page=2`) while preserving all semantic query parameters.

### Decision: Composite Authorization Scope
- **Choice**: Construct two distinct sub-scopes: `user_scope` and `client_scope`.
  - **User Scope**: `anon` (unauthenticated), `superuser`, `owner`, or `groups:<sorted_names>`.
  - **Client Scope**: `client:none`, `apikey:<key_string>`, or `origin:<origin_pattern>`.
- **Rationale**: Accurately reflects Shareabouts dual-axis permission model (`check_data_permission`), guaranteeing that privileged API keys and specific CORS origins have isolated cache entries while anonymous public visitors share a single common cache bucket.

### Decision: Semicolon Delimiter
- **Choice**: Join top-level cache key elements with `;`:
  `{prefix};{format};{canonical_query};{user_scope};{client_scope}`
- **Rationale**: Semicolons prevent collision with colons used internally inside URL paths, query parameters, format names, or scope tags.

## Risks / Trade-offs

- **[Risk] Existing Cache Entries Invalidation**: Switching the key format will invalidate existing cached keys in Redis on deployment.
  - **Mitigation**: Keys naturally warm up within seconds on initial traffic. Old keys expire automatically per Redis TTL (`settings.API_CACHE_TIMEOUT`).

## Migration Plan

1. Implement format negotiation helper and query canonicalizer in `CachedResourceMixin`.
2. Update `get_cache_key()` to construct the semicolon-delimited composite key.
3. Add comprehensive unit tests covering format normalization, query canonicalization, and client/user auth scoping.
4. Deploy to dev/prod.
