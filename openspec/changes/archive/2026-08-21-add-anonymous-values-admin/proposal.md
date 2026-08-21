## Why

While anonymous demographic and survey values can now be submitted and retrieved via the API, administrators and dataset owners cannot currently inspect, manage, search, or clone anonymous data records within the Django admin interface. Adding Django admin support and dataset cloning integration allows administrators to manage anonymous values alongside other dataset resources without compromising the structural separation and privacy of the underlying data.

## What Changes

- **AnonymousValues Admin Registration**: Register `AnonymousValues` in Django admin with a changelist showing ID, dataset owner, dataset slug, set name, and formatted JSON data.
- **Filtering & Search**: Support filtering by dataset slug (`DataSetFilter`) and `set_name`, and searching across `set_name` and `data`.
- **Owner-Scoped Querysets**: Restrict non-superusers to viewing and managing anonymous values for datasets they own.
- **Dataset Admin Integration**: Add an `anonymous_values` changelist link to `DataSetAdmin`'s readonly fields, linking directly to the dataset's filtered anonymous records.
- **JSON Editing Widget**: Use `PrettyAceWidget` with form validation for editing anonymous JSON data blobs in the admin change form.
- **Dataset Cloning Support**: Inherit `CloneableModelMixin` on `AnonymousValues`, integrate with `DataSet.clone_related`, and update background celery cloning tasks to copy anonymous records when cloning a dataset.
- **Model Verbose Names**: Set `verbose_name` and `verbose_name_plural` to `"Anonymous values"` on `AnonymousValues.Meta`.

## Capabilities

### New Capabilities
- `anonymous-data-admin`: Exposes `AnonymousValues` in the Django admin with changelist filtering, searching, owner-scoped access, JSON editing, and navigation links from `DataSetAdmin`.

### Modified Capabilities
- `anonymous-data-model`: Updates `AnonymousValues` to be cloneable (`CloneableModelMixin`) and integrated into `DataSet.clone_related` when cloning datasets.

## Impact

- **Models**: `AnonymousValues` and `DataSet.clone_related` in `sa_api_v2/models/core.py`.
- **Admin**: `sa_api_v2/admin.py` adding `AnonymousValuesAdmin` and updating `DataSetAdmin`.
- **Celery Tasks**: `sa_api_v2/tasks.py` adding `anonymous_values` to `clone_related_dataset_data` prefetch list.
- **Dependencies & DB**: No new database migrations or package dependencies required.
