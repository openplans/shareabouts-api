## 1. Model & Migration

- [x] 1.1 Create `AnonymousValues` model in `sa_api_v2/models/` with UUID PK (`uuid.uuid4`), `dataset` FK to `DataSet` (CASCADE), `set_name` TextField (indexed), and `data` JSONBField. Ensure no FK to Place/Submission and no timestamp fields.
- [x] 1.2 Generate and verify Django migration for the `AnonymousValues` table. Confirm UUID PK, CASCADE FK, and `set_name` index in the generated migration.
- [x] 1.3 Write model-level tests: UUID PK generation, JSONB data with mixed types (strings, arrays, objects), cascade delete on DataSet, place deletion does not affect anonymous data, `set_name` values for places vs submissions.

## 2. Write Path — Anonymous Prefix Stripping

- [x] 2.1 Extend `DataBlobProcessor.to_internal_value` (in `serializers.py`) to extract `anonymous_`-prefixed fields from incoming data, strip the prefix from key names, and store them as `self._anonymous_data` on the serializer instance. Ensure the stripped fields are removed from the data blob passed to the model.
- [x] 2.2 In `SubmittedThingSerializer.create` (or equivalent), after saving the place/submission, create an `AnonymousValues` record within the same database transaction using the dataset and set_name from the created object. Skip creation if `_anonymous_data` is empty or all values are null/empty-string.
- [x] 2.3 Determine the correct `set_name` for the `AnonymousValues` record: `"places"` for place creation, `submission.set_name` for submission creation. Ensure this is passed through correctly from the view/serializer context.
- [x] 2.4 Write tests for the write path:
  - Place creation with `anonymous_` attributes → place data blob excludes anonymous fields, `AnonymousValues` row created with correct `set_name="places"` and prefix-stripped data
  - Submission creation with `anonymous_` attributes → submission data blob excludes anonymous fields, `AnonymousValues` row created with correct `set_name`
  - Complex anonymous values (arrays, objects) are preserved in JSONB
  - No `AnonymousValues` row when all anonymous values are null/empty
  - Mixed null and non-null anonymous values → row created with all keys (including null ones)
  - Creation response excludes anonymous attributes
  - Failed creation (validation error) → no `AnonymousValues` row persisted (atomicity)
  - Request with no `anonymous_` attributes → no `AnonymousValues` row created

## 3. Read Path — Anonymous Data Summaries on Existing Views

- [x] 3.1 Add `INCLUDE_ANONYMOUS_PARAM = 'include_anonymous'` to `params.py` alongside existing `INCLUDE_PRIVATE_PARAM`.
- [x] 3.2 Update `IsAllowedByDataPermissions` (in `views/base_views.py`) to treat `include_anonymous` as a protected data access request (same as `include_private`/`include_invisible`), returning 401/403 for unauthorized requests.
- [x] 3.3 Extend `DataSetPlaceSetSummarySerializer` to include `anonymous_data: { length, url }` in the places summary when `include_anonymous` is set and the requester has permission. The URL should point to `.../{ds}/places/anonymous`.
- [x] 3.4 Extend `DataSetSubmissionSetSummarySerializer` to include `anonymous_data: { length, url }` in each submission set summary when `include_anonymous` is set. The URL should point to `.../{ds}/{set_name}/anonymous`.
- [x] 3.5 Extend `PaginatedResultsPagination.get_paginated_response` and `FeatureCollectionPagination.get_paginated_response` to accept and inject an optional `anonymous_data` summary into the response envelope.
- [x] 3.6 Update `PlaceListView` to compute and pass the anonymous data summary (count + URL for `set_name="places"`) to the paginator when `include_anonymous` is set.
- [x] 3.7 Update `DataSetSubmissionListView` to compute and pass the anonymous data summary (count + URL for the relevant `set_name`) to the paginator when `include_anonymous` is set.
- [x] 3.8 Update `SubmissionListView` (place-specific) to compute and pass the anonymous data summary when `include_anonymous` is set. The URL must point to the dataset-level anonymous endpoint, and the length must reflect the total count across the entire dataset for that `set_name`.
- [x] 3.9 Ensure `PlaceInstanceView` and `SubmissionInstanceView` (detail views) do NOT include any anonymous data, even when `include_anonymous` is in the query string.
- [x] 3.10 Ensure submission set entries within individual place features (the `submission_sets` property on each GeoJSON feature) do NOT include anonymous data information even when `include_anonymous` is set.
- [x] 3.11 Write tests for the read summaries:
  - Dataset detail with/without `include_anonymous` → `anonymous_data` present/absent in places and submission_sets summaries
  - Place list with/without `include_anonymous` → top-level `anonymous_data` present/absent; per-feature `submission_sets` exclude `anonymous_data`
  - Dataset-level submission set list with `include_anonymous` → `anonymous_data` summary present
  - Place-specific submission set list with `include_anonymous` → `anonymous_data` summary with dataset-level URL
  - Detail views ignore `include_anonymous`
  - Permission enforcement: unauthenticated → 401; authenticated but unauthorized → 403; dataset owner → success; API key with `can_access_protected` → success
  - Default requests (no `include_anonymous`) incur no `AnonymousValues` query

## 4. Read Path — Dedicated Anonymous Data Endpoints

- [x] 4.1 Create `AnonymousValuesSerializer` that serializes `AnonymousValues.data` as the top-level JSON object (not wrapped in `{ "id": ..., "data": ... }`). Each result item is the raw JSONB blob.
- [x] 4.2 Create `PlaceAnonymousDataListView` — a read-only `ListAPIView` for `GET /api/v2/{owner}/datasets/{ds}/places/anonymous`. Filters `AnonymousValues` by `(dataset, set_name="places")`. Uses `PaginatedResultsPagination`. Requires `can_access_protected` permission.
- [x] 4.3 Create `SubmissionSetAnonymousDataListView` — a read-only `ListAPIView` for `GET /api/v2/{owner}/datasets/{ds}/{set_name}/anonymous`. Filters `AnonymousValues` by `(dataset, set_name)`. Uses `PaginatedResultsPagination`. Requires `can_access_protected` permission.
- [x] 4.4 Register URL patterns in `sa_api_v2/urls.py`:
  - `places/anonymous` before `places/(?P<place_id>\d+)` routes
  - `(?P<submission_set_name>[^/]+)/anonymous` before the catch-all `DataSetSubmissionListView` pattern
- [x] 4.5 Write tests for the dedicated endpoints:
  - GET returns paginated anonymous data with correct `metadata` and `results`
  - Results are raw JSONB blobs (no wrapping)
  - Pagination works correctly (page 1, page 2, page_size param)
  - POST/PUT/PATCH/DELETE → 405 Method Not Allowed
  - Permission enforcement: unauthorized → 403; unauthenticated → 401; dataset owner → success
  - Empty dataset → `results: []`, `length: 0`
  - `places/anonymous` returns only `set_name="places"` rows
  - `{set_name}/anonymous` returns only rows matching that `set_name`

## 5. Documentation

- [x] 5.1 Update `PlaceListView` docstring to document `include_anonymous` GET param and `anonymous_` prefix on POST body.
- [x] 5.2 Update `PlaceInstanceView` docstring to document `anonymous_` prefix on PUT/POST body.
- [x] 5.3 Update `DataSetSubmissionListView` docstring to document `include_anonymous` GET param.
- [x] 5.4 Update `SubmissionListView` docstring to document `include_anonymous` GET param and `anonymous_` prefix on POST body.
- [x] 5.5 Update `DataSetInstanceView` docstring to document `include_anonymous` GET param.
- [x] 5.6 Add full docstrings to `PlaceAnonymousDataListView` and `SubmissionSetAnonymousDataListView`.
- [x] 5.7 Update `doc/API_v2.md` to describe the anonymous data feature: `anonymous_` write convention, `include_anonymous` read param, and dedicated anonymous data endpoints.
