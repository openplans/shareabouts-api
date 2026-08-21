## 1. Model & Cloning Integration

- [x] 1.1 Inherit `CloneableModelMixin` on `AnonymousValues` and set `verbose_name = 'Anonymous values'` and `verbose_name_plural = 'Anonymous values'` in `AnonymousValues.Meta`.
- [x] 1.2 Update `DataSet.clone_related` in `sa_api_v2/models/core.py` to clone all associated `anonymous_values` onto the target dataset.
- [x] 1.3 Update `clone_related_dataset_data` in `sa_api_v2/tasks.py` to include `'anonymous_values'` in the queryset `prefetch_related` list.
- [x] 1.4 Write unit tests for `AnonymousValues` cloning and `DataSet.clone_related` integration.

## 2. AnonymousValues Admin

- [x] 2.1 Create `AnonymousValuesAdmin` class in `sa_api_v2/admin.py` with `list_display = ('id', 'owner', 'dataset', 'set_name', 'data')` and custom column helper methods.
- [x] 2.2 Configure `list_filter = ('set_name', DataSetFilter)` and `search_fields = ('set_name', 'data')` on `AnonymousValuesAdmin`.
- [x] 2.3 Configure `raw_id_fields = ('dataset',)` and `readonly_fields = ('id',)` on `AnonymousValuesAdmin`.
- [x] 2.4 Implement `get_queryset` on `AnonymousValuesAdmin` to restrict non-superusers to `dataset__owner=request.user`.
- [x] 2.5 Implement `get_form` on `AnonymousValuesAdmin` with `PrettyAceWidget(mode='json', ...)` and JSON validation on the `data` field.
- [x] 2.6 Register `AnonymousValues` with `admin.site.register(models.AnonymousValues, AnonymousValuesAdmin)`.

## 3. DataSet Admin Navigation

- [x] 3.1 Add `anonymous_values(self, instance)` helper method on `DataSetAdmin` to render an HTML link to `/admin/sa_api_v2/anonymousvalues/?dataset={slug}`.
- [x] 3.2 Add `'anonymous_values'` to `DataSetAdmin.readonly_fields`.

## 4. Automated Tests

- [x] 4.1 Write admin tests covering:
  - `AnonymousValuesAdmin` changelist rendering, custom columns (`owner`, `dataset`), filters, and search
  - `AnonymousValuesAdmin.get_queryset` scoping for superusers vs dataset owners
  - `AnonymousValuesAdmin` form validation rejecting invalid JSON
  - `DataSetAdmin` change form rendering the `anonymous_values` link
  - Dataset cloning duplicating all associated `AnonymousValues`
