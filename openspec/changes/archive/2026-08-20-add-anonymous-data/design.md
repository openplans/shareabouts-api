## Context

See [proposal.md](proposal.md) for motivation. The current codebase provides two data tiers on places and submissions:

- **Public data**: arbitrary keys in the `data` blob (a `TextField` storing JSON)
- **Private data**: keys prefixed with `private_` in the same blob, stripped at serialization by `DataBlobProcessor.explode_data_blob` unless `include_private` is set

The `private_` pattern is purely access-control: data remains in the same row and is joinable to the submitter via database access. The anonymous data feature introduces structural separation via a new model with no FK to places or submissions.

Key existing patterns this design builds on:
- `DataBlobProcessor` ([serializers.py:265-325](../../src/sa_api_v2/serializers.py)) — strips `private_` keys; we extend this for `anonymous_`
- `DataSetPlaceSetSummarySerializer` / `DataSetSubmissionSetSummarySerializer` ([serializers.py:597-685](../../src/sa_api_v2/serializers.py)) — `{ length, url }` summaries on dataset view; we replicate this pattern for anonymous data summaries
- `PaginatedResultsPagination` / `FeatureCollectionPagination` ([serializers.py:1083-1098](../../src/sa_api_v2/serializers.py)) — inject `metadata` into responses; we extend these to optionally inject `anonymous_data`
- `IsAllowedByDataPermissions` ([views/base_views.py:240-287](../../src/sa_api_v2/views/base_views.py)) — checks `can_access_protected` for `include_private`/`include_invisible`; we add `include_anonymous` to the same gate

## Goals / Non-Goals

**Goals:**
- Structural separation: anonymous data has no join path to places/submissions at the database level
- Consistent API surface: `anonymous_` prefix mirrors the `private_` convention; `include_anonymous` mirrors `include_private`
- Paginated access: anonymous data served from dedicated endpoints with standard pagination
- Minimal permission model change: reuse `can_access_protected`

**Non-Goals:**
- Server-side deduplication of anonymous data (client-managed)
- A separate `can_access_anonymous` permission field (may add later, but coarse-grained `can_access_protected` is sufficient for now)
- Updating or deleting individual anonymous data rows (structurally impossible by design — no link back)
- Anonymous data on detail views (single place or submission)

## Decisions

### 1. New Django model with JSONB (not TextField)

**Decision**: Use a native PostgreSQL JSONB field for `AnonymousValues.data`, even though the existing `SubmittedThing.data` uses `TextField` with manual JSON serialization.

**Rationale**: JSONB supports indexing and querying within the JSON blob, which may be useful for future aggregate analysis (e.g., count by age range). Since this is a new model with no legacy compatibility constraints, there's no reason to inherit the TextField pattern.

**Alternative**: Use `TextField` for consistency with `SubmittedThing`. Rejected because JSONB is strictly better for structured data and this is a greenfield model.

### 2. Anonymous prefix stripping in DataBlobProcessor

**Decision**: Extend the existing `DataBlobProcessor.to_internal_value` method to extract `anonymous_`-prefixed fields from the incoming data and store them separately on the serializer instance (e.g., `self._anonymous_data`). The actual `AnonymousValues` creation happens in the serializer's `create` method (or a post-save hook) within the same transaction.

**Rationale**: This keeps the stripping logic co-located with the existing `private_` handling and ensures the place/submission data blob is clean before it reaches the model's `save`. Using the serializer's `create` method for the `AnonymousValues` write ensures atomicity via the existing transaction context.

**Alternative**: Strip in the view layer. Rejected because data transformation is a serializer concern and the `private_` precedent is in the serializer.

### 3. Summaries via pagination class extension (not view override)

**Decision**: Extend `PaginatedResultsPagination` and `FeatureCollectionPagination` to accept an optional `anonymous_data` kwarg and inject it into the paginated response. Views pass the summary data to the paginator when `include_anonymous` is set.

**Rationale**: The paginator already controls the response envelope shape (`metadata`, `results`/`features`). Adding `anonymous_data` at this level keeps the response construction centralized. Views are responsible for computing the count and URL, then handing it to the paginator.

**Alternative**: Override `list()` on each view to manually patch the response data. Rejected because it duplicates logic across multiple views and the paginator already handles envelope construction.

### 4. Dataset-level anonymous endpoint URLs only

**Decision**: Anonymous data endpoints exist only at the dataset level:
- `GET /api/v2/{owner}/datasets/{ds}/places/anonymous`
- `GET /api/v2/{owner}/datasets/{ds}/{set_name}/anonymous`

No place-specific anonymous data URLs (e.g., `.../places/{id}/{set_name}/anonymous`).

**Rationale**: Anonymous data is keyed by `(dataset, set_name)` with no place FK. A place-scoped URL would be semantically wrong and could imply place-level filtering that doesn't exist. Place-specific submission set list views include the anonymous summary but link to the dataset-level endpoint.

### 5. URL routing: explicit pattern before catch-all

**Decision**: Register the new anonymous data URL patterns before the catch-all `DataSetSubmissionListView` pattern in `urls.py`. The `places/anonymous` route also precedes `places/(?P<place_id>\d+)` for clarity, though `anonymous` wouldn't match `\d+`.

**Rationale**: Django's URL resolver uses first-match. The catch-all pattern `(?P<submission_set_name>[^/]+)` on line 66 of `urls.py` would match `{set_name}/anonymous` as a submission list for a set literally named `"{set_name}"` with a `pk_list` filter. Placing the anonymous routes first prevents this.

### 6. Permission reuse: can_access_protected

**Decision**: Gate `include_anonymous` and the anonymous data endpoints behind the existing `can_access_protected` flag on `DataPermission`. No new permission field.

**Rationale**: Adding a new field (`can_access_anonymous`) would require a migration, admin updates, and permission-checking logic changes. The coarse-grained approach is adequate: in practice, users with access to anonymous data typically also have access to private data (e.g., dataset owners, analytics partners). Can be refined later if a use case emerges.

**Alternative**: New `can_access_anonymous` boolean. Deferred — would add complexity now with no immediate need.

## Risks / Trade-offs

- **[Re-identification in small datasets]** → Accepted tradeoff. Storing all anonymous attributes in one row enables cross-tabulation but increases re-identification risk when dataset size is small. Mitigated by: this is a known property of any demographic collection, and the alternative (one row per attribute) makes analysis impractical.

- **[Extra count query on include_anonymous]** → Low risk. The `COUNT(*)` on `AnonymousValues` filtered by `(dataset_id, set_name)` is cheap with the index on `set_name` and FK on `dataset`. Only runs when `include_anonymous` is requested.

- **[Catch-all URL collision]** → Mitigated by route ordering. If a submission set is literally named `"anonymous"`, the anonymous data endpoint would shadow it. This is acceptable — `"anonymous"` is a reserved name for this feature. Document this.

- **[No rollback for anonymous data]** → By design. Once anonymous data is written, there's no way to associate it back to a submission for correction or deletion. This is the core privacy guarantee, not a bug.

## Migration Plan

1. Add Django migration creating `AnonymousValues` table with UUID PK, `dataset_id` FK (CASCADE), `set_name` (indexed), `data` (JSONB)
2. Deploy migration — no data migration needed, table starts empty
3. Deploy code changes — feature is opt-in via `anonymous_` prefix on writes and `include_anonymous` on reads
4. No rollback concerns: the feature is additive and the new table can be dropped without affecting existing data
