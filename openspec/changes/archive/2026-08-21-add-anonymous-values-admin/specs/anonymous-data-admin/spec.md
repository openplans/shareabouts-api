## Purpose

Provides Django admin interface integration for AnonymousValues, allowing administrators and dataset owners to inspect, filter, search, view, edit, and navigate to anonymous records.

## ADDED Requirements

### Requirement: AnonymousValues model admin registration and changelist display
The system SHALL register `AnonymousValues` in the Django admin site via `AnonymousValuesAdmin`. The changelist view SHALL display the following columns:
- `id`: UUID of the record
- `owner`: username of the dataset's owner
- `dataset`: slug of the associated dataset
- `set_name`: logical submission set name (e.g. `"places"`, `"comments"`)
- `data`: formatted JSON content of the anonymous data blob

#### Scenario: Admin changelist shows anonymous record columns
- **WHEN** an admin navigates to the `AnonymousValues` changelist in Django admin
- **THEN** each row SHALL display the record's UUID, the dataset owner's username, the dataset slug, the set name, and the data blob

### Requirement: Changelist filtering and search
The `AnonymousValuesAdmin` SHALL support filtering and full-text searching:
- Filtering by dataset slug via `DataSetFilter`
- Filtering by `set_name`
- Searching by `set_name` and `data` content

#### Scenario: Filter anonymous values by dataset slug
- **WHEN** an admin filters by a dataset slug in the `AnonymousValues` changelist
- **THEN** only `AnonymousValues` belonging to that dataset SHALL be displayed

#### Scenario: Filter anonymous values by set_name
- **WHEN** an admin filters by a `set_name` (e.g. `"comments"`) in the `AnonymousValues` changelist
- **THEN** only `AnonymousValues` with that `set_name` SHALL be displayed

#### Scenario: Search anonymous values by data content
- **WHEN** an admin searches for a keyword that appears in `data` (e.g. `"Asian"` or `"25-34"`)
- **THEN** matching `AnonymousValues` records SHALL be returned in search results

### Requirement: Owner-scoped access for non-superusers
For users who are not superusers, `AnonymousValuesAdmin` SHALL restrict the queryset to records where `dataset__owner=request.user`.

#### Scenario: Superuser sees all anonymous records
- **WHEN** a superuser accesses the `AnonymousValues` admin changelist
- **THEN** all `AnonymousValues` across all datasets SHALL be visible

#### Scenario: Non-superuser sees only owned dataset anonymous records
- **WHEN** an authenticated non-superuser accesses the `AnonymousValues` admin changelist
- **THEN** only `AnonymousValues` belonging to datasets owned by that user SHALL be visible

### Requirement: Change form with JSON editing
The `AnonymousValuesAdmin` change and add form SHALL allow viewing and editing `AnonymousValues` fields:
- `id` SHALL be a read-only field
- `dataset` SHALL use a raw ID lookup field (`raw_id_fields`)
- `data` SHALL use a JSON editing widget (`PrettyAceWidget`) with JSON syntax validation on save

#### Scenario: Editing anonymous values in admin form
- **WHEN** an admin edits an `AnonymousValues` record with valid JSON in the `data` field
- **THEN** the changes SHALL be validated and saved to the database

#### Scenario: Invalid JSON in data field is rejected
- **WHEN** an admin submits invalid JSON in the `data` field
- **THEN** form validation SHALL raise an error and prevent saving

### Requirement: Dataset admin navigation link
`DataSetAdmin` SHALL include an `anonymous_values` read-only field that renders an HTML link pointing to the `AnonymousValues` changelist filtered by that dataset's slug (`/admin/sa_api_v2/anonymousvalues/?dataset={slug}`).

#### Scenario: Dataset change form renders anonymous values link
- **WHEN** an admin views a `DataSet` change form in Django admin
- **THEN** the `anonymous_values` read-only field SHALL render a link to `/admin/sa_api_v2/anonymousvalues/?dataset={slug}`
