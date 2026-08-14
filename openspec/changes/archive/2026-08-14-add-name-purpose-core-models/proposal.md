## Why

Currently, API keys, CORS origins, and user groups in Shareabouts API do not include descriptive metadata fields like `display_name` or `purpose` (while `Group` has a short identifier `name` field). This makes it difficult for administrators and API consumers to identify why a specific API key was issued, what an origin pattern is for, or what a group's human-readable intent is in the admin UI and API responses. Adding `display_name` and `purpose` fields to `ApiKey`, `Origin`, and `Group` provides clarity when managing permissions and keys for specific integration purposes without conflicting with existing fields.

## What Changes

- Add optional `display_name` (CharField, max_length=128) and `purpose` (TextField) fields to `ApiKey` in `src/sa_api_v2/apikey/models.py`.
- Add optional `display_name` and `purpose` fields to `Origin` in `src/sa_api_v2/cors/models.py`.
- Add optional `display_name` and `purpose` fields to `Group` in `src/sa_api_v2/models/profiles.py` (preserving existing `name` field).
- Update string representations (`__unicode__` / `__str__`) for `ApiKey`, `Origin`, and `Group` to default to `display_name` with fallback to `key`, `pattern`, or `name`.
- Update REST Framework serializers: `ApiKeySerializer`, `OriginSerializer`, and `SimpleGroupSerializer` include `display_name` and `purpose`, while `GroupSerializer` excludes `display_name` and `purpose`.
- Update Django admin representations and inline admins (`InlineApiKeyAdmin`, `InlineOriginAdmin`, `InlineGroupAdmin`) to make `display_name` and `purpose` editable and displayed in list views.
- Generate and include database migrations for these model schema changes.

## Capabilities

### New Capabilities
- `model-metadata`: Support `display_name` and `purpose` fields on `ApiKey`, `Origin`, and `Group` models to describe their identity and purpose.

### Modified Capabilities

## Impact

- **Models**: `ApiKey` (`src/sa_api_v2/apikey/models.py`), `Origin` (`src/sa_api_v2/cors/models.py`), `Group` (`src/sa_api_v2/models/profiles.py`).
- **Serializers**: `src/sa_api_v2/serializers.py`.
- **Admin**: `src/sa_api_v2/apikey/admin.py`, `src/sa_api_v2/cors/admin.py`, `src/sa_api_v2/admin.py`.
- **Database**: New Django migrations under `src/sa_api_v2/migrations/`.
