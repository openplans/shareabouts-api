# anonymous-data-write Specification

## Purpose

Defines the write-path behavior for anonymous data: how `anonymous_`-prefixed attributes are stripped from place and submission creation requests and stored as structurally separate `AnonymousValues` rows.

## Requirements

### Requirement: Strip anonymous-prefixed attributes on place creation
When a place creation request includes attributes with the `anonymous_` prefix, the system SHALL:
1. Remove those attributes from the place's data blob before saving the place
2. Create an `AnonymousValues` record with `set_name="places"` and the stripped attributes (with prefix removed) as the `data` JSONB

The place SHALL be saved with only public and `private_`-prefixed attributes in its data blob.

#### Scenario: Place created with anonymous attributes
- **WHEN** a POST request creates a place with properties `{"location_type": "suggestion", "private_email": "j@example.com", "anonymous_age": "25-34", "anonymous_race": "Asian"}`
- **THEN** the place's data blob SHALL contain `{"location_type": "suggestion", "private_email": "j@example.com"}`
- **AND** an `AnonymousValues` record SHALL be created with `set_name="places"` and `data={"age": "25-34", "race": "Asian"}`

#### Scenario: Place created without anonymous attributes
- **WHEN** a POST request creates a place with properties `{"location_type": "suggestion", "description": "Add bike lane"}`
- **THEN** the place's data blob SHALL contain all provided attributes
- **AND** no `AnonymousValues` record SHALL be created

### Requirement: Strip anonymous-prefixed attributes on submission creation
When a submission creation request includes attributes with the `anonymous_` prefix, the system SHALL:
1. Remove those attributes from the submission's data blob before saving the submission
2. Create an `AnonymousValues` record with `set_name` matching the submission's `set_name` and the stripped attributes (with prefix removed) as the `data` JSONB

#### Scenario: Submission created with anonymous attributes
- **WHEN** a POST request creates a submission in the `"comments"` set with data `{"text": "Great idea", "anonymous_age": "18-24"}`
- **THEN** the submission's data blob SHALL contain `{"text": "Great idea"}`
- **AND** an `AnonymousValues` record SHALL be created with `set_name="comments"` and `data={"age": "18-24"}`

#### Scenario: Submission created with complex anonymous values
- **WHEN** a POST request creates a submission in the `"ballots"` set with data `{"idhash": "abc123", "has_voted": true, "anonymous_proposals": ["A", "B", "C"]}`
- **THEN** the submission's data blob SHALL contain `{"idhash": "abc123", "has_voted": true}`
- **AND** an `AnonymousValues` record SHALL be created with `set_name="ballots"` and `data={"proposals": ["A", "B", "C"]}`

### Requirement: Prefix stripping removes the anonymous_ prefix from attribute names
When storing anonymous attributes in the `AnonymousValues.data` blob, the `anonymous_` prefix SHALL be removed from the attribute name. For example, `anonymous_age` becomes `age`, `anonymous_proposals` becomes `proposals`.

#### Scenario: Prefix removed from stored attribute names
- **WHEN** a request includes `"anonymous_ethnicity": "Hispanic or Latino"`
- **THEN** the `AnonymousValues.data` blob SHALL contain `{"ethnicity": "Hispanic or Latino"}` (not `{"anonymous_ethnicity": "Hispanic or Latino"}`)

### Requirement: No AnonymousValues row for empty anonymous data
If a request contains `anonymous_`-prefixed attributes but all values are empty, null, or the empty string, the system SHALL NOT create an `AnonymousValues` row.

#### Scenario: All anonymous values are null
- **WHEN** a POST request creates a place with `{"location_type": "park", "anonymous_age": null, "anonymous_race": ""}`
- **THEN** no `AnonymousValues` record SHALL be created

#### Scenario: Some anonymous values are non-empty
- **WHEN** a POST request creates a place with `{"location_type": "park", "anonymous_age": "25-34", "anonymous_race": null}`
- **THEN** an `AnonymousValues` record SHALL be created with `data={"age": "25-34", "race": null}`

### Requirement: Anonymous data creation is atomic with place/submission creation
The creation of the `AnonymousValues` record SHALL occur within the same database transaction as the place or submission creation. If the place or submission creation fails, no `AnonymousValues` row SHALL be persisted.

#### Scenario: Failed place creation does not create anonymous data
- **WHEN** a place creation request with anonymous attributes fails validation
- **THEN** no `AnonymousValues` record SHALL be created

### Requirement: Anonymous attributes not returned in creation response
The response to a place or submission creation request SHALL NOT include the `anonymous_`-prefixed attributes. The response SHALL show only the saved place/submission data (public and private attributes).

#### Scenario: Creation response excludes anonymous data
- **WHEN** a place is successfully created with `anonymous_age` and `anonymous_race` attributes
- **THEN** the response body SHALL NOT contain `anonymous_age`, `anonymous_race`, `age`, or `race`
