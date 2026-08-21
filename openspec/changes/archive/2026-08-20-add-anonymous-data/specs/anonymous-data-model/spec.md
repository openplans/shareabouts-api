## Purpose

Defines the `AnonymousValues` data model that provides structural separation of privacy-sensitive data from places and submissions, ensuring no join path exists between anonymous data and the originating submission.

## ADDED Requirements

### Requirement: AnonymousValues model structure
The system SHALL store anonymous data in an `AnonymousValues` model with the following fields:
- `id`: UUID primary key, auto-generated
- `dataset`: Foreign key to `DataSet` with CASCADE delete
- `set_name`: Text field, indexed, identifying the logical submission set (e.g., `"comments"`, `"support"`, `"places"`)
- `data`: JSONB field containing the anonymous attribute values

The model SHALL NOT have:
- Any foreign key to `Place` or `Submission`
- Any timestamp field (`created_datetime`, `updated_datetime`)

#### Scenario: AnonymousValues row is created with UUID
- **WHEN** an `AnonymousValues` record is created
- **THEN** it SHALL have an auto-generated UUID as its primary key (not a sequential integer)

#### Scenario: No link to place or submission
- **WHEN** an `AnonymousValues` record exists in the database
- **THEN** there SHALL be no foreign key, column, or join path that connects it to any `Place` or `Submission` record

### Requirement: JSONB data supports any JSON-serializable type
The `data` field SHALL accept any JSON-serializable value as attribute values, including strings, numbers, booleans, arrays, and nested objects.

#### Scenario: Array value in anonymous data
- **WHEN** an `AnonymousValues` record is created with `data` containing `{"proposals": ["A", "B", "C"]}`
- **THEN** the stored value SHALL preserve the array structure and be retrievable as-is

#### Scenario: Mixed value types in anonymous data
- **WHEN** an `AnonymousValues` record is created with `data` containing `{"age": "25-34", "score": 42, "opted_in": true}`
- **THEN** all value types SHALL be preserved (string, integer, boolean)

### Requirement: Cascade delete on DataSet
When a `DataSet` is deleted, all `AnonymousValues` rows associated with that dataset SHALL be deleted.

#### Scenario: Dataset deletion cascades to anonymous data
- **WHEN** a `DataSet` with associated `AnonymousValues` rows is deleted
- **THEN** all `AnonymousValues` rows with that dataset's foreign key SHALL be deleted

### Requirement: Place deletion does not affect anonymous data
Deleting a `Place` or `Submission` SHALL NOT delete any `AnonymousValues` rows, because no relationship exists between them.

#### Scenario: Place deleted, anonymous data unaffected
- **WHEN** a `Place` is deleted from a dataset that also has `AnonymousValues` rows with `set_name="places"`
- **THEN** the `AnonymousValues` rows SHALL remain unchanged

### Requirement: Set name matches submission set naming
The `set_name` field SHALL use the same values as `Submission.set_name` for submission-originated anonymous data. For anonymous data originating from place creation, the `set_name` SHALL be `"places"`.

#### Scenario: Anonymous data from place creation uses set_name "places"
- **WHEN** anonymous data is created as part of a place creation request
- **THEN** the `AnonymousValues.set_name` SHALL be `"places"`

#### Scenario: Anonymous data from submission creation uses submission's set_name
- **WHEN** anonymous data is created as part of a submission to the `"comments"` submission set
- **THEN** the `AnonymousValues.set_name` SHALL be `"comments"`
