## ADDED Requirements

### Requirement: AnonymousValues is cloneable with datasets
`AnonymousValues` SHALL implement model cloning via `CloneableModelMixin`. When a `DataSet` is cloned, all `AnonymousValues` associated with the source dataset SHALL be cloned onto the new dataset with a new UUID primary key.

#### Scenario: Dataset clone copies anonymous values
- **WHEN** a dataset with associated `AnonymousValues` records is cloned
- **THEN** matching `AnonymousValues` records SHALL be created for the new dataset with identical `set_name` and `data` blobs, each assigned a distinct auto-generated UUID

### Requirement: Model verbose naming
The `AnonymousValues` model Meta SHALL define `verbose_name` and `verbose_name_plural` both as `"Anonymous values"`.

#### Scenario: Model Meta verbose names
- **WHEN** the model Meta options for `AnonymousValues` are evaluated
- **THEN** `verbose_name` SHALL be `"Anonymous values"`
- **AND** `verbose_name_plural` SHALL be `"Anonymous values"`
