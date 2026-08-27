## Why

Currently, cache metakeys (which track the set of active cache keys for a dataset or resource collection) are stored as serialized, pickled Python `set` objects in standard Django cache key-value strings. Under concurrent traffic spikes, simultaneous writes to the same metakey suffer from race conditions where workers overwrite each other's pickled sets, leading to dropped keys, broken invalidation, and spurious cache misses. Replacing this with native Redis set operations (`SADD`, `SISMEMBER`, `SMEMBERS`) provides atomic O(1) membership management, eliminates concurrency clobbering, and avoids transferring growing sets across the network.

## What Changes

- Introduce a `SetCache` abstraction in `src/sa_api_v2/cache.py` with comprehensive docstrings explaining its purpose, using native Redis set operations (`SADD`, `SISMEMBER`, `SMEMBERS`, `SREM`, `EXPIRE`) when Redis is active, with seamless fallback for non-Redis backends (such as in-memory test caches).
- Update `CachedResourceMixin.dispatch()` to check key membership atomically via `SetCache.is_member()`.
- Update `CachedResourceMixin.cache_response()` to register keys atomically via `SetCache.add()` with pipelined TTL refreshes.
- Update cache clearing methods (`Cache.get_keys_with_prefixes()`) to retrieve all collection members via `SetCache.get_members()`.

## Capabilities

### New Capabilities
- `redis-set-caching`: Atomic Redis-native set operations for tracking and invalidating resource cache keysets.

### Modified Capabilities

## Impact

- **Affected Code**: `src/sa_api_v2/cache.py` and `src/sa_api_v2/views/base_views.py`.
- **Concurrency & Reliability**: Prevents silent cache misses and race conditions during high concurrent traffic.
- **Dependencies**: Uses `django_redis.cache.RedisCache` client when available; fully backward-compatible with standard Django test cache backends.
