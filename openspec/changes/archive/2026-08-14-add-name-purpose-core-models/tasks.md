## 1. Model Updates & Migrations

- [x] 1.1 Add `display_name` and `purpose` fields and update `__unicode__`/`__str__` fallback logic on `ApiKey` in `src/sa_api_v2/apikey/models.py`
- [x] 1.2 Add `display_name` and `purpose` fields and update `__unicode__`/`__str__` fallback logic on `Origin` in `src/sa_api_v2/cors/models.py`
- [x] 1.3 Add `display_name` and `purpose` fields and update `__unicode__`/`__str__` fallback logic on `Group` in `src/sa_api_v2/models/profiles.py`
- [x] 1.4 Generate and verify Django migrations for model changes

## 2. Serializers & Admin Integration

- [x] 2.1 Update `ApiKeySerializer`, `OriginSerializer`, `SimpleGroupSerializer` (including `display_name` & `purpose`), and `GroupSerializer` (excluding `display_name` & `purpose`) in `src/sa_api_v2/serializers.py`
- [x] 2.2 Update `ApiKeyAdmin` and `InlineApiKeyAdmin` in `src/sa_api_v2/apikey/admin.py` and `src/sa_api_v2/admin.py` to display and edit `display_name` and `purpose`
- [x] 2.3 Update `OriginAdmin` and `InlineOriginAdmin` in `src/sa_api_v2/cors/admin.py` and `src/sa_api_v2/admin.py` to display and edit `display_name` and `purpose`
- [x] 2.4 Update `GroupAdmin` and `InlineGroupAdmin` in `src/sa_api_v2/admin.py` to display and edit `display_name` and `purpose`

## 3. Testing & Validation

- [x] 3.1 Write tests for `ApiKey`, `Origin`, and `Group` model metadata, string representation fallbacks, and cloning behavior
- [x] 3.2 Write tests for API endpoints/serializers verifying `GroupSerializer` excludes and `SimpleGroupSerializer` includes `display_name` and `purpose`
- [x] 3.3 Run the full test suite to ensure all tests pass without regression
