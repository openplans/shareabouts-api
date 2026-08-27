## 1. SetCache Abstraction & Unit Tests

- [x] 1.1 Implement `SetCache` class in `src/sa_api_v2/cache.py` with detailed docstring, native Redis driver integration (`sadd`, `sismember`, `smembers`, `srem`, `expire`), WRONGTYPE handling, and non-Redis fallback
- [x] 1.2 Add unit tests for `SetCache` verifying atomic addition, membership checking, member retrieval, deletion, and fallback behavior

## 2. Integration into Views & Invalidation

- [x] 2.1 Update `CachedResourceMixin.dispatch()` in `src/sa_api_v2/views/base_views.py` to verify key tracking via `set_cache.is_member()`
- [x] 2.2 Update `CachedResourceMixin.cache_response()` in `src/sa_api_v2/views/base_views.py` to register keys via `set_cache.add()`
- [x] 2.3 Update `Cache.get_keys_with_prefixes()` in `src/sa_api_v2/cache.py` to query tracked keys via `set_cache.get_members()`

## 3. Verification

- [x] 3.1 Run complete test suite (`test_views`, `test_caching`) to ensure zero regressions across all cached endpoints
