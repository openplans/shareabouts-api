## Purpose

Provides atomic Redis-native set operations for tracking, verifying, and invalidating collections of cached API response keys without concurrency race conditions or set serialization overhead.

## ADDED Requirements

### Requirement: Atomic Cache Key Set Registration
The API cache system SHALL register generated cache keys into collection metakey sets using atomic set addition (`SADD`) without deserializing or rewriting existing set members.

#### Scenario: Concurrent cache writes to same collection
- **WHEN** multiple concurrent requests finish rendering different pages of the same resource collection
- **THEN** each request atomically adds its cache key to the metakey set in Redis without overwriting or dropping keys registered by other concurrent workers

### Requirement: Atomic Cache Key Membership Check
The API cache system SHALL verify whether a specific cache key belongs to an active collection metakey using atomic membership testing (`SISMEMBER`) in O(1) time without loading or transferring the entire keyset.

#### Scenario: Cache hit verification
- **WHEN** an incoming GET request checks whether a cached response is still tracked in the active metakey set
- **THEN** the cache system performs an atomic membership query against Redis and serves the cached response if present

### Requirement: Set TTL Maintenance
The API cache system SHALL update the expiration TTL of the metakey set whenever a cache key is registered, ensuring the set lifetime extends to match the newest cached member.

#### Scenario: Maintaining set lifespan on additions
- **WHEN** a new cache key is registered into an existing metakey set
- **THEN** the expiration TTL of the metakey set is reset to the configured API cache timeout

### Requirement: Collection Invalidation via Set Members
The API cache system SHALL retrieve all active cache keys associated with a metakey using set member retrieval (`SMEMBERS`) when invalidating a collection, deleting all member keys and the metakey itself.

#### Scenario: Cache clearing on model update
- **WHEN** a dataset, place, or submission is modified or deleted
- **THEN** the cache system retrieves all tracked cache keys from the associated metakeys and clears them from the cache

### Requirement: Non-Redis Cache Fallback
The API cache system SHALL support a fallback mode for non-Redis cache backends (such as in-memory test caches) that maintains identical set operations semantics.

#### Scenario: Running under local test cache
- **WHEN** requests execute in an environment using Django's LocMemCache or other standard cache backends
- **THEN** set operations complete successfully using Python set fallback structures
