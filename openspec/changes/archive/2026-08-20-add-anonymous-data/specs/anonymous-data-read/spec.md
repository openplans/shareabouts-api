## Purpose

Defines the read-path behavior for anonymous data: summary metadata on existing list views via `include_anonymous`, dedicated paginated endpoints for full anonymous data retrieval, and permission enforcement.

## ADDED Requirements

### Requirement: Anonymous data summary on dataset detail view
When `?include_anonymous` is present on a dataset detail request and the requester has `can_access_protected` permission, the response SHALL include an `anonymous_data` object within each place set and submission set summary. The `anonymous_data` object SHALL contain:
- `length`: the count of `AnonymousValues` rows for that `(dataset, set_name)`
- `url`: the URL of the dedicated anonymous data endpoint for that set

#### Scenario: Dataset detail with include_anonymous
- **WHEN** an authorized request is made to `GET /api/v2/{owner}/datasets/{ds}/?include_anonymous`
- **THEN** the `places` summary SHALL include `anonymous_data: { length: <count>, url: ".../{ds}/places/anonymous" }`
- **AND** each entry in `submission_sets` SHALL include `anonymous_data: { length: <count>, url: ".../{ds}/{set_name}/anonymous" }`

#### Scenario: Dataset detail without include_anonymous
- **WHEN** a request is made to `GET /api/v2/{owner}/datasets/{ds}/` without `include_anonymous`
- **THEN** the response SHALL NOT contain any `anonymous_data` fields

### Requirement: Anonymous data summary on place list view
When `?include_anonymous` is present on a place list request and the requester has `can_access_protected` permission, the top-level response SHALL include an `anonymous_data` summary for the `"places"` set_name. Submission set entries within individual place features SHALL NOT include anonymous data information.

#### Scenario: Place list with include_anonymous
- **WHEN** an authorized request is made to `GET /api/v2/{owner}/datasets/{ds}/places?include_anonymous`
- **THEN** the top-level response SHALL include `anonymous_data: { length: <count>, url: ".../{ds}/places/anonymous" }`
- **AND** the `submission_sets` property on each feature SHALL NOT contain any `anonymous_data` fields

#### Scenario: Place list without include_anonymous
- **WHEN** a request is made to `GET /api/v2/{owner}/datasets/{ds}/places` without `include_anonymous`
- **THEN** the response SHALL NOT contain any `anonymous_data` fields

### Requirement: Anonymous data summary on dataset-level submission set list view
When `?include_anonymous` is present on a dataset-level submission set list request and the requester has `can_access_protected` permission, the response SHALL include an `anonymous_data` summary.

#### Scenario: Dataset-level submission set list with include_anonymous
- **WHEN** an authorized request is made to `GET /api/v2/{owner}/datasets/{ds}/{set_name}?include_anonymous`
- **THEN** the response SHALL include `anonymous_data: { length: <count>, url: ".../{ds}/{set_name}/anonymous" }`

### Requirement: Anonymous data summary on place-specific submission set list view
When `?include_anonymous` is present on a place-specific submission set list request and the requester has `can_access_protected` permission, the response SHALL include an `anonymous_data` summary. The `url` SHALL point to the **dataset-level** anonymous data endpoint, not a place-specific one. The `length` SHALL reflect the total count across the entire dataset for that set_name.

#### Scenario: Place-specific submission set list with include_anonymous
- **WHEN** an authorized request is made to `GET /api/v2/{owner}/datasets/{ds}/places/{place_id}/{set_name}?include_anonymous`
- **THEN** the response SHALL include `anonymous_data: { length: <count>, url: ".../{ds}/{set_name}/anonymous" }`
- **AND** the `url` SHALL be the dataset-level anonymous data endpoint (not scoped to the place)
- **AND** the `length` SHALL be the total count of anonymous data for that `set_name` across the entire dataset

### Requirement: No anonymous data on individual place or submission detail views
Anonymous data SHALL NOT be included in any form on individual place detail (`GET .../places/{id}`) or submission detail (`GET .../{set_name}/{id}`) responses, regardless of query parameters.

#### Scenario: Place detail view ignores include_anonymous
- **WHEN** a request is made to `GET /api/v2/{owner}/datasets/{ds}/places/{id}?include_anonymous`
- **THEN** the response SHALL NOT contain any `anonymous_data` fields

#### Scenario: Submission detail view ignores include_anonymous
- **WHEN** a request is made to `GET /api/v2/{owner}/datasets/{ds}/places/{place_id}/{set_name}/{id}?include_anonymous`
- **THEN** the response SHALL NOT contain any `anonymous_data` fields

### Requirement: Dedicated paginated anonymous data endpoints
The system SHALL provide dedicated read-only endpoints for retrieving full anonymous data:
- `GET /api/v2/{owner}/datasets/{ds}/places/anonymous` — anonymous data with `set_name="places"`
- `GET /api/v2/{owner}/datasets/{ds}/{set_name}/anonymous` — anonymous data with the specified `set_name`

These endpoints SHALL return paginated responses using the standard pagination format (`metadata` + `results`). Each item in `results` SHALL be the `data` JSONB blob from an `AnonymousValues` row, serialized directly as a JSON object.

#### Scenario: Retrieve paginated anonymous data for a submission set
- **WHEN** an authorized request is made to `GET /api/v2/{owner}/datasets/{ds}/comments/anonymous`
- **THEN** the response SHALL contain `metadata` (with `length`, `next`, `previous`, `page`, `num_pages`) and `results` (array of data blobs)
- **AND** each item in `results` SHALL be a JSON object representing one `AnonymousValues.data` blob (e.g., `{"age": "25-34", "race": "Asian"}`)

#### Scenario: Retrieve anonymous data for places
- **WHEN** an authorized request is made to `GET /api/v2/{owner}/datasets/{ds}/places/anonymous`
- **THEN** the response SHALL contain paginated anonymous data rows with `set_name="places"`

#### Scenario: Anonymous data endpoint with pagination
- **WHEN** there are 250 anonymous data rows for `set_name="comments"` and the default page size is 100
- **THEN** `GET .../comments/anonymous` SHALL return page 1 with 100 results and `metadata.num_pages` of 3
- **AND** `metadata.next` SHALL point to `...comments/anonymous?page=2`

#### Scenario: Anonymous data endpoint is read-only
- **WHEN** a POST, PUT, PATCH, or DELETE request is made to an anonymous data endpoint
- **THEN** the system SHALL respond with 405 Method Not Allowed

### Requirement: Permission enforcement for include_anonymous
When `?include_anonymous` is present on a request, the system SHALL check that the requester has `can_access_protected` permission on the relevant `DataPermission`. If the requester does not have this permission, the system SHALL respond with 401 (if unauthenticated) or 403 (if authenticated but unauthorized), consistent with how `include_private` and `include_invisible` are handled.

#### Scenario: Unauthenticated request with include_anonymous
- **WHEN** an unauthenticated request includes `?include_anonymous`
- **THEN** the system SHALL respond with 401 Unauthorized

#### Scenario: Authenticated but unauthorized request with include_anonymous
- **WHEN** an authenticated user without `can_access_protected` permission requests `?include_anonymous`
- **THEN** the system SHALL respond with 403 Forbidden

#### Scenario: Authorized request with include_anonymous
- **WHEN** a request from the dataset owner or a user with `can_access_protected` permission includes `?include_anonymous`
- **THEN** the anonymous data summary SHALL be included in the response

### Requirement: Permission enforcement for anonymous data endpoints
Requests to the dedicated anonymous data endpoints SHALL require `can_access_protected` permission. The dataset owner and superusers always have access.

#### Scenario: Unauthorized request to anonymous data endpoint
- **WHEN** a user without `can_access_protected` permission requests `GET .../comments/anonymous`
- **THEN** the system SHALL respond with 403 Forbidden

#### Scenario: Dataset owner accesses anonymous data endpoint
- **WHEN** the dataset owner requests `GET .../comments/anonymous`
- **THEN** the response SHALL contain the paginated anonymous data

### Requirement: Anonymous data count query only on include_anonymous
The additional database query to count `AnonymousValues` rows for the summary SHALL only be executed when `include_anonymous` is present in the request. Default requests without `include_anonymous` SHALL incur no additional query overhead.

#### Scenario: Default request has no anonymous data overhead
- **WHEN** a request is made to a place list or submission set list without `include_anonymous`
- **THEN** no query against the `AnonymousValues` table SHALL be executed
