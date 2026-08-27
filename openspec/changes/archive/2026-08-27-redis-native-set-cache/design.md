## Context

In the Shareabouts API, `CachedResourceMixin` and model cache classes maintain metakeys (e.g. `datasets:23_keys` or `/api/v2/owner/datasets/ds/places_keys`) to track the set of active cache keys associated with a resource collection. When an entity is modified, these keys are retrieved and cleared. Currently, metakeys store a pickled Python `set` in standard cache keys. Under multi-process concurrent workers (e.g. Gunicorn), concurrent updates clobber each other.

## Goals / Non-Goals

**Goals:**
- Provide atomic, O(1) set additions (`SADD`) and membership tests (`SISMEMBER`) via Redis native data types.
- Ensure zero concurrency race conditions when multiple workers cache pages of the same resource simultaneously.
- Provide a `SetCache` abstraction with comprehensive docstrings explaining its purpose, methods, and fallback mechanics.
- Support seamless fallback for non-Redis cache backends (e.g. `LocMemCache` during unit tests).
- Automatically extend the TTL on metakey sets whenever new members are added.

**Non-Goals:**
- Changing cache key naming conventions or format prefixes.
- Modifying non-set cache operations (e.g. serialized payload storage).

## Decisions

### Decision 1: Create a Dedicated `SetCache` Utility Class in `src/sa_api_v2/cache.py`
- **Choice**: Encapsulate all set operations in a `SetCache` helper class equipped with a detailed docstring explaining its purpose, native Redis driver integration, and non-Redis fallback.
- **Rationale**: Isolates backend-specific Redis operations from view and model code.
- **Alternatives Considered**: 
  - Direct Redis calls inside `CachedResourceMixin`: Clutters view code and breaks when tests run with `LocMemCache`.

### Decision 2: Access Raw Redis Client via `django-redis` with `make_key` Mapping
- **Choice**: Inspect `django_cache.cache.client.get_client()` to access the underlying `redis.Redis` client. When executing native set commands, format keys with `cache.make_key(set_key)` to respect Django cache versioning and prefixes.
- **Rationale**: Ensures native Redis set operations operate on the exact same physical Redis keys as Django's standard `cache.get/set/delete`.

### Decision 3: Pipelined `SADD` and `EXPIRE`
- **Choice**: When adding a member to a set, execute `SADD` and `EXPIRE` together using a Redis pipeline (`pipe.sadd(...); pipe.expire(...); pipe.execute()`).
- **Rationale**: Keeps the set alive as long as its newest cached entry in a single network roundtrip without risk of orphaned unbounded metakeys.

### Decision 4: Transparent LocMemCache / Non-Redis Fallback
- **Choice**: If `_get_redis_client()` returns `None`, fall back to standard `cache.get(set_key)` / `cache.set(set_key, set_obj)` operations.
- **Rationale**: Ensures test suites and local development environments without Redis run without friction.

## Risks / Trade-offs

- **[Risk] Redis Byte Decoding**: Redis returns set members as byte strings (`bytes`) by default.
  - **Mitigation**: `SetCache.get_members()` decodes all members to `utf-8` strings so key deletion matches string identifiers.
- **[Risk] Type Mismatch in Redis Key**: If a previous deployment stored a string/pickle at the metakey and we attempt `SADD`, Redis will return a `WRONGTYPE` error.
  - **Mitigation**: `SetCache.add()` can catch `ResponseError` / `WRONGTYPE`, delete the old key, and re-initialize as a native set.
