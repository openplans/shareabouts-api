## Context

See `proposal.md` for overall motivation.

`ApiKey` (`src/sa_api_v2/apikey/models.py`), `Origin` (`src/sa_api_v2/cors/models.py`), and `Group` (`src/sa_api_v2/models/profiles.py`) are models used to manage API authentication and authorization settings for datasets. Currently, `Group` has a `name` field (short identifier/slug), but none of `ApiKey`, `Origin`, or `Group` have `display_name` or `purpose` fields.

## Goals / Non-Goals

**Goals:**
- Add `display_name` (CharField, max_length=128, blank=True, default='') and `purpose` (TextField, blank=True, default='') fields to `ApiKey`, `Origin`, and `Group`.
- Update `__unicode__` / `__str__` on `ApiKey`, `Origin`, and `Group` to default to `display_name`, falling back to `key`, `pattern`, and `name` respectively.
- Update serializers in `src/sa_api_v2/serializers.py`: `ApiKeySerializer`, `OriginSerializer`, and `SimpleGroupSerializer` include `display_name` and `purpose`; `GroupSerializer` excludes `display_name` and `purpose` (along with `submitters` and `id`).
- Update Django admin configurations: `ApiKeyAdmin`, `OriginAdmin`, and `GroupAdmin` include `display_name` and `purpose` in `list_display` and `search_fields`. `InlineApiKeyAdmin`, `InlineOriginAdmin`, and `InlineGroupAdmin` allow editing `display_name` and `purpose`.
- Generate Django schema migration file.

**Non-Goals:**
- Making `display_name` or `purpose` required fields for existing or new instances (they must remain optional with default empty strings to avoid breaking existing data or API clients).
- Modifying authentication logic or permission evaluation behavior based on `display_name` or `purpose`.

## Decisions

1. **Field definitions and defaults**:
   - `display_name`: `models.CharField(max_length=128, blank=True, default='')` for `ApiKey`, `Origin`, and `Group`. (`Group` retains its existing `name` field as well).
   - `purpose`: `models.TextField(blank=True, default='')` for `ApiKey`, `Origin`, and `Group`.
   - *Rationale*: Naming the field `display_name` avoids conflict with `Group.name`. Using `blank=True, default=''` allows backwards compatibility for existing records without requiring NULL handling or breaking non-null DB constraints.

2. **String representations**:
   - `ApiKey.__unicode__`: `return self.display_name or self.key`
   - `Origin.__unicode__`: `return self.display_name or self.pattern`
   - `Group.__unicode__`: `return '%s in %s' % (self.display_name or self.name, self.dataset.slug)`
   - *Rationale*: Provides human-friendly labels when available while preserving clear identifying fallbacks.

3. **API Serializers update**:
   - `ApiKeySerializer` and `OriginSerializer`: include `display_name` and `purpose`.
   - `BaseGroupSerializer`: `exclude = ('submitters', 'id')`.
   - `SimpleGroupSerializer`: inherits `BaseGroupSerializer.Meta`, `exclude = ('id', 'dataset', 'submitters')` (includes `display_name` and `purpose`).
   - `GroupSerializer`: `exclude = ('id', 'submitters', 'display_name', 'purpose')`.
   - *Rationale*: Allows `SimpleGroupSerializer` to expose metadata attributes while `GroupSerializer` excludes them as requested.

4. **Admin UI enhancements**:
   - `ApiKeyAdmin`: `list_display = ('key', 'display_name', 'purpose', 'dataset', 'logged_ip', 'last_used')`, `search_fields = ('key', 'display_name', 'purpose')`.
   - `OriginAdmin`: `list_display = ('pattern', 'display_name', 'purpose', 'dataset', 'logged_ip', 'last_used')`, `search_fields = ('pattern', 'display_name', 'purpose')`.
   - `GroupAdmin`: `list_display = ('name', 'display_name', 'purpose', 'dataset')`, `search_fields = ('name', 'display_name', 'purpose')`.
   - `InlineApiKeyAdmin`, `InlineOriginAdmin`, `InlineGroupAdmin`: Ensure `fields` / `fields` lists render `display_name` and `purpose` as editable fields in inline dataset forms.
   - *Rationale*: Enhances admin usability and searchability for permission resources across both model admin and inline dataset admin interfaces.

5. **Migration generation**:
   - Create a migration using Django's `makemigrations` (or hand-craft if needed) in `src/sa_api_v2/migrations/`.

## Risks / Trade-offs

- **[Risk]** Large dataset with many API keys/origins causing slow migration runtime.
  - *Mitigation*: Fields have static default values (`''`), which makes migration trivial and fast in PostgreSQL.
