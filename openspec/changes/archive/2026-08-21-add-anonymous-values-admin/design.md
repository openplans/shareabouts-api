## Context

`AnonymousValues` records store privacy-sensitive demographic/survey data separated from `Place` and `Submission` records. While API endpoints allow protected querying, administrators currently have no interface in Django admin to view or manage these records.

See `proposal.md` for motivation and `specs/` for normative requirements.

## Goals / Non-Goals

**Goals:**
- Provide a full-featured `AnonymousValuesAdmin` with changelist filtering, searching, owner scoping, and JSON editing.
- Provide direct navigation from `DataSetAdmin` to the dataset's anonymous values.
- Support dataset cloning for `AnonymousValues` via `CloneableModelMixin` and `DataSet.clone_related`.
- Ensure non-superusers can only access anonymous values for datasets they own.

**Non-Goals:**
- Inline editing of anonymous values directly inside `DataSetAdmin` (high volume of records makes changelist filtering more performant and scalable).
- Any link or association from `PlaceAdmin` or `SubmissionAdmin` to `AnonymousValues` (violates data separation principles).

## Decisions

### Decision 1: Changelist Link on DataSetAdmin vs Tabular Inline
- **Chosen**: Add an `anonymous_values` readonly link field on `DataSetAdmin` that points to `/admin/sa_api_v2/anonymousvalues/?dataset={slug}`.
- **Rationale**: Datasets may have thousands of anonymous records. Inlining them inside the dataset change form would significantly degrade page load performance. A filtered changelist view gives admins pagination, search, and bulk operations.
- **Alternatives Considered**: Tabular inline on `DataSetAdmin` (rejected due to performance and clutter).

### Decision 2: Custom owner and dataset columns on AnonymousValuesAdmin
- **Chosen**: Implement `owner(self, obj)` returning `obj.dataset.owner.username` and `dataset(self, obj)` returning `obj.dataset.slug` on `AnonymousValuesAdmin.list_display`.
- **Rationale**: Gives administrators clear context of which user owns the dataset and which dataset slug the record belongs to at a glance.

### Decision 3: JSON Editing with PrettyAceWidget
- **Chosen**: Use `PrettyAceWidget` with form-level JSON validation in `AnonymousValuesAdmin.get_form`.
- **Rationale**: Keeps consistency with `SubmittedThingAdmin`, providing syntax highlighting, auto-formatting, and error checking for JSON blobs.

### Decision 4: Dataset Cloning via CloneableModelMixin
- **Chosen**: Have `AnonymousValues` inherit from `CloneableModelMixin`, call `anon_val.clone(overrides={'dataset': onto})` in `DataSet.clone_related`, and add `'anonymous_values'` to `clone_related_dataset_data` prefetch list in `tasks.py`.
- **Rationale**: Ensures cloned datasets created via Django admin object actions (`clone_dataset`) duplicate all related data including anonymous records with fresh UUID primary keys.

## Risks / Trade-offs

- **[Search Performance on large JSONB datasets]** → PostgreSQL handles JSONB search efficiently. The admin search is scoped by owner/dataset filters.
- **[Accidental data association]** → Admin views maintain complete relational separation (no links to places or submissions).
