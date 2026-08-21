## Why

Shareabouts supports public and private data tiers on places and submissions, but `private_` fields are only access-control separated — they remain in the data blob and are joinable to the submitter at the database level. For privacy-sensitive demographic surveys (e.g., participatory budgeting voting, post-vote demographic surveys), we need a third tier where data is **structurally decoupled** from the originating place or submission, making correlation impossible without resorting to data forensics tactics, even with direct database access. This is particularly important for government-run civic engagement tools where data may be subject to public records requests or subpoenas.

## What Changes

- **New `AnonymousValues` model** with UUID PK, dataset FK, `set_name`, and JSONB `data` — deliberately no FK to Place/Submission, no timestamp
- **Write path**: `anonymous_`-prefixed attributes on place/submission creation are stripped from the submission data and stored in a separate `AnonymousValues` row with no link back
- **Read path (summaries)**: `?include_anonymous` on dataset, place list, and submission set list views returns `{ length, url }` summaries pointing to dedicated anonymous data endpoints
- **Read path (full data)**: New paginated endpoints at `.../{set_name}/anonymous` and `.../places/anonymous` serve the anonymous data rows
- **Permissions**: Access gated by existing `can_access_protected` flag on `DataPermission`; unauthorized requests receive 401/403
- **Browsable API documentation**: View docstrings updated for all affected endpoints
- **No individual-level exposure**: Anonymous data never appears on place or submission detail views

## Capabilities

### New Capabilities
- `anonymous-data-model`: The `AnonymousValues` data model, migration, and storage logic
- `anonymous-data-write`: Stripping `anonymous_`-prefixed fields during place/submission creation and storing them as `AnonymousValues` rows
- `anonymous-data-read`: Summaries on existing list views via `include_anonymous`, dedicated paginated anonymous data endpoints, and permission enforcement
- `anonymous-data-docs`: Browsable API docstring updates and standalone documentation for the anonymous data feature

### Modified Capabilities
_(none — no existing specs are affected)_

## Impact

- **Models**: New `AnonymousValues` model + migration in `sa_api_v2`
- **Serializers**: `DataBlobProcessor` modified for `anonymous_` prefix stripping; new serializer for anonymous data; `DataSetPlaceSetSummarySerializer` and `DataSetSubmissionSetSummarySerializer` updated for anonymous summaries; pagination classes updated to inject anonymous summary into responses
- **Views**: New `PlaceAnonymousDataListView` and `SubmissionSetAnonymousDataListView`; existing place/submission list views modified to support `include_anonymous`
- **URLs**: Two new URL patterns added before catch-all patterns in `sa_api_v2/urls.py`
- **Permissions**: `include_anonymous` treated as protected data access (401/403 via `IsAllowedByDataPermissions`)
- **Tests**: New test coverage for model, write path, read path, permissions, and edge cases
- **Documentation**: View docstrings + `doc/API_v2.md`
