# model-metadata Specification

## Purpose

Provides identifying metadata (display_name and purpose) on API keys, origins, and groups to allow administrators and API clients to understand their intended use.

## Requirements

### Requirement: ApiKey includes display_name and purpose
The ApiKey model SHALL support optional `display_name` and `purpose` string fields. Its string representation SHALL default to `display_name` and fall back to `key` when `display_name` is empty.

#### Scenario: ApiKey created with display_name and purpose
- **WHEN** an ApiKey is created with a display_name and purpose
- **THEN** the display_name and purpose values are stored on the ApiKey instance and returned in API responses and admin views

#### Scenario: ApiKey string representation fallback
- **WHEN** string representation (`__unicode__`/`__str__`) of an ApiKey is evaluated
- **THEN** it returns `display_name` if present, or `key` if `display_name` is empty

#### Scenario: ApiKey cloned retains display_name and purpose
- **WHEN** an ApiKey with display_name and purpose is cloned to a new dataset
- **THEN** the cloned ApiKey retains the display_name and purpose values of the original ApiKey

### Requirement: Origin includes display_name and purpose
The Origin model SHALL support optional `display_name` and `purpose` string fields. Its string representation SHALL default to `display_name` and fall back to `pattern` when `display_name` is empty.

#### Scenario: Origin created with display_name and purpose
- **WHEN** an Origin is created with a display_name and purpose
- **THEN** the display_name and purpose values are stored on the Origin instance and returned in API responses and admin views

#### Scenario: Origin string representation fallback
- **WHEN** string representation (`__unicode__`/`__str__`) of an Origin is evaluated
- **THEN** it returns `display_name` if present, or `pattern` if `display_name` is empty

#### Scenario: Origin cloned retains display_name and purpose
- **WHEN** an Origin with display_name and purpose is cloned to a new dataset
- **THEN** the cloned Origin retains the display_name and purpose values of the original Origin

### Requirement: Group includes display_name and purpose
The Group model SHALL support optional `display_name` and `purpose` string fields alongside its existing `name` field. Its string representation SHALL use `display_name` if present, falling back to `name`.

#### Scenario: Group created with display_name and purpose
- **WHEN** a Group is created with a display_name and purpose
- **THEN** the display_name and purpose values are stored on the Group instance and returned in API responses and admin views

#### Scenario: Group string representation fallback
- **WHEN** string representation (`__unicode__`/`__str__`) of a Group is evaluated
- **THEN** it uses `display_name` if present, or `name` if `display_name` is empty

#### Scenario: Group cloned retains display_name and purpose
- **WHEN** a Group with display_name and purpose is cloned to a new dataset
- **THEN** the cloned Group retains the display_name and purpose values of the original Group

### Requirement: API serializers control display_name and purpose field inclusion
ApiKeySerializer, OriginSerializer, and SimpleGroupSerializer SHALL include `display_name` and `purpose`. GroupSerializer SHALL explicitly exclude `display_name` and `purpose` (in addition to `submitters` and `id`).

#### Scenario: GroupSerializer excludes display_name and purpose
- **WHEN** a Group is serialized via `GroupSerializer`
- **THEN** `display_name` and `purpose` fields are excluded from the output

#### Scenario: SimpleGroupSerializer includes display_name and purpose
- **WHEN** a Group is serialized via `SimpleGroupSerializer`
- **THEN** `display_name` and `purpose` fields are included in the output

### Requirement: Django admin views and inline forms render display_name and purpose
`ApiKeyAdmin`, `OriginAdmin`, and `GroupAdmin` SHALL include `display_name` and `purpose` in `list_display`. `InlineApiKeyAdmin`, `InlineOriginAdmin`, and `InlineGroupAdmin` SHALL allow editing `display_name` and `purpose`.

#### Scenario: Inline admin forms permit editing metadata
- **WHEN** editing dataset inlines in Django admin for API keys, origins, or groups
- **THEN** `display_name` and `purpose` fields are rendered and editable
