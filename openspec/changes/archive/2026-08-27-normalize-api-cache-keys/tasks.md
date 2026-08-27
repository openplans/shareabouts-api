## 1. Test Suite Preparation

- [x] 1.1 Add unit tests in `src/sa_api_v2/tests/test_views.py` covering format normalization, query parameter sorting, composite user/client scopes, and semicolon delimiters

## 2. Cache Key Implementation

- [x] 2.1 Implement query string canonicalization helper in `CachedResourceMixin`
- [x] 2.2 Implement response format normalization helper in `CachedResourceMixin`
- [x] 2.3 Implement composite user and client authorization scope resolution in `CachedResourceMixin`
- [x] 2.4 Update `get_cache_key()` in `CachedResourceMixin` to assemble the semicolon-delimited key

## 3. Verification

- [x] 3.1 Run Django test suite to verify that all cache key tests and existing API view tests pass
