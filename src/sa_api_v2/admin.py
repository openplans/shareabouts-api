"""
Basic behind-the-scenes maintenance for superusers,
via django.contrib.admin.
"""

import models
from django.contrib.gis import admin
from .apikey.models import ApiKey


class SubmittedThingAdmin(admin.OSMGeoAdmin):
    date_hierarchy = 'created_datetime'
    list_display = ('id', 'created_datetime', 'updated_datetime', 'submitter_name', 'dataset')
    list_filter = ('dataset',)
    search_fields = ('submitter__username', 'data',)

    raw_id_fields = ('submitter', 'dataset')

    def submitter_name(self, obj):
        return obj.submitter.username if obj.submitter else None


class InlineApiKeyAdmin(admin.StackedInline):
    model = ApiKey.datasets.through


class InlineGroupAdmin(admin.StackedInline):
    model = models.Group
    filter_horizontal = ('submitters',)
    extra = 1


class DataSetAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'slug', 'owner')
    prepopulated_fields = {'slug': ['display_name']}
    inlines = [InlineApiKeyAdmin, InlineGroupAdmin]


class PlaceAdmin(SubmittedThingAdmin):
    model = models.Place


class SubmissionSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_filter = ('name',)


class SubmissionAdmin(SubmittedThingAdmin):
    model = models.Submission

    list_display = SubmittedThingAdmin.list_display + ('place', 'set_',)
    list_filter = ('parent__name',) + SubmittedThingAdmin.list_filter
    list_select_related = ('parent',)
    search_fields = ('parent__name',) + SubmittedThingAdmin.search_fields

    def set_(self, obj):
        return obj.parent.name
    set_.short_description = 'Set'
    set_.admin_order_field = 'parent__name'

    def place(self, obj):
        return obj.parent.place_id
    place.admin_order_field = 'parent__place'


class ActionAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_datetime'
    list_display = ('id', 'created_datetime', 'action', 'submitter_name')

    def submitter_name(self, obj):
        return obj.submitter.username if obj.submitter else None


class InlineGroupPermissionAdmin(admin.TabularInline):
    model = models.GroupPermission
    extra = 0


class GroupAdmin(admin.ModelAdmin):
    raw_id_fields = ('dataset',)
    filter_horizontal = ('submitters',)
    inlines = [InlineGroupPermissionAdmin]

    class Media:
        js = (
            'admin/js/jquery-1.11.0.min.js',
            'admin/js/jquery-ui-1.10.4.min.js',
            'admin/js/admin-list-reorder.js',
        )


admin.site.register(models.DataSet, DataSetAdmin)
admin.site.register(models.Place, PlaceAdmin)
admin.site.register(models.SubmissionSet, SubmissionSetAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.Group, GroupAdmin)
