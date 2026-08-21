## Purpose

Defines the documentation requirements for the anonymous data feature, including browsable API docstring updates and standalone API documentation.

## ADDED Requirements

### Requirement: Browsable API documents include_anonymous parameter
View classes that support `?include_anonymous` SHALL include documentation for this parameter in their class docstring, following the existing pattern used for `include_private` and `include_invisible`.

#### Scenario: PlaceListView docstring documents include_anonymous and anonymous_ prefix
- **WHEN** a user views the browsable API for the place list endpoint
- **THEN** the documentation SHALL describe the `include_anonymous` GET parameter and its behavior
- **AND** the documentation SHALL describe the `anonymous_` prefix for POST request body attributes

#### Scenario: DataSetSubmissionListView docstring documents include_anonymous
- **WHEN** a user views the browsable API for the dataset-level submission set list endpoint
- **THEN** the documentation SHALL describe the `include_anonymous` GET parameter

#### Scenario: SubmissionListView docstring documents include_anonymous and anonymous_ prefix
- **WHEN** a user views the browsable API for the place-specific submission list endpoint
- **THEN** the documentation SHALL describe the `include_anonymous` GET parameter and the `anonymous_` prefix for POST

#### Scenario: DataSetInstanceView docstring documents include_anonymous
- **WHEN** a user views the browsable API for the dataset detail endpoint
- **THEN** the documentation SHALL describe the `include_anonymous` GET parameter

### Requirement: New anonymous data endpoints have full docstrings
The new `PlaceAnonymousDataListView` and `SubmissionSetAnonymousDataListView` view classes SHALL have descriptive class docstrings that explain the endpoint's purpose, authentication, and response format.

#### Scenario: Anonymous data endpoint browsable API documentation
- **WHEN** a user views the browsable API for an anonymous data list endpoint
- **THEN** the documentation SHALL describe the endpoint as read-only, explain what data it returns, and note the authentication/permission requirements

### Requirement: Standalone API documentation updated
The standalone documentation at `doc/API_v2.md` SHALL be updated to describe the anonymous data feature, including the `anonymous_` prefix convention, the `include_anonymous` parameter, and the dedicated anonymous data endpoints.

#### Scenario: API_v2.md documents anonymous data
- **WHEN** a developer reads `doc/API_v2.md`
- **THEN** they SHALL find documentation covering the anonymous data write convention (`anonymous_` prefix), read behavior (`include_anonymous`), and the dedicated anonymous data endpoints
