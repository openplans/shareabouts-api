"""
Basic behind-the-scenes maintenance for superusers,
via django.contrib.admin.
"""

import json
import models
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.gis import admin
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.utils.html import escape
from django_ace import AceWidget
from .apikey.models import ApiKey
from .cors.models import Origin


class SubmissionSetFilter (SimpleListFilter):
    """
    Used to filter a list of submissions by type (set name).
    """
    title = 'Submission Set'
    parameter_name = 'set'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        qs = qs.order_by('parent__name').distinct('parent__name').values('parent__name')
        return [(elem['parent__name'], elem['parent__name']) for elem in qs]

    def queryset(self, request, qs):
        parent__name = self.value()
        if parent__name:
            qs = qs.filter(parent__name=parent__name)
        return qs


class DataSetFilter (SimpleListFilter):
    """
    Used to filter a list of submitted things by dataset slug.
    """
    title = 'Dataset'
    parameter_name = 'dataset'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        qs = qs.order_by('dataset__slug').distinct('dataset__slug').values('dataset__slug')
        return [(elem['dataset__slug'], elem['dataset__slug']) for elem in qs]

    def queryset(self, request, qs):
        dataset__slug = self.value()
        if dataset__slug:
            qs = qs.filter(dataset__slug=dataset__slug)
        return qs


class InlineAttachmentAdmin(admin.StackedInline):
    model = models.Attachment
    extra = 0


class PrettyAceWidget (AceWidget):
    def render(self, name, value, attrs=None):
        if value:
            try:
                # If we can prettify the JSON, we should
                value = json.dumps(json.loads(value), indent=2)
            except ValueError:
                # If we cannot, then we should still display the value
                pass
        return super(PrettyAceWidget, self).render(name, value, attrs=attrs)


class SubmittedThingAdmin(admin.OSMGeoAdmin):
    date_hierarchy = 'created_datetime'
    inlines = (InlineAttachmentAdmin,)
    list_display = ('id', 'created_datetime', 'submitter_name', 'dataset', 'visible', 'data')
    list_editable = ('visible',)
    list_filter = (DataSetFilter,)
    search_fields = ('submitter__username', 'data',)

    raw_id_fields = ('submitter', 'dataset')

    def submitter_name(self, obj):
        return obj.submitter.username if obj.submitter else None

    def get_queryset(self, request):
        qs = super(SubmittedThingAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(dataset__owner=user)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        FormWithJSONCleaning = super(SubmittedThingAdmin, self).get_form(request, obj=obj, **kwargs)

        def clean_json_blob(form):
            data = form.cleaned_data['data']
            try:
                json.loads(data)
            except ValueError as e:
                raise ValidationError(e)
            return data

        FormWithJSONCleaning.clean_data = clean_json_blob
        FormWithJSONCleaning.base_fields['data'].widget = PrettyAceWidget(mode='json', width='100%', wordwrap=True, theme='jsoneditor')
        return FormWithJSONCleaning

    def save_model(self, request, obj, form, change):
        # Make changes through the admin silently.
        obj.save(silent=True)


class InlineApiKeyAdmin(admin.StackedInline):
    model = ApiKey
    # raw_id_fields = ['apikey']
    extra = 0
    readonly_fields = ('edit_url',)

    def permissions_list(self, instance):
        if instance.pk:
            return '<ul>%s</ul>' % ''.join(['<li>%s</li>' % (escape(permission),) for permission in instance.permissions.all()])
        else:
            return ''

    def edit_url(self, instance):
        if instance.pk is None:
            return '(You must save your dataset before you can edit the permissions on your API key.)'
        else:
            return (
                '<a href="%s"><strong>Edit permissions</strong></a>' % (reverse('admin:apikey_apikey_change', args=[instance.pk]))
                + self.permissions_list(instance)
            )
    edit_url.allow_tags = True


class InlineOriginAdmin(admin.StackedInline):
    model = Origin
    # raw_id_fields = ['origin']
    extra = 0
    readonly_fields = ('edit_url',)

    def permissions_list(self, instance):
        if instance.pk:
            return '<ul>%s</ul>' % ''.join(['<li>%s</li>' % (escape(permission),) for permission in instance.permissions.all()])
        else:
            return ''

    def edit_url(self, instance):
        if instance.pk is None:
            return '(You must save your dataset before you can edit the permissions on your origin.)'
        else:
            return (
                '<a href="%s"><strong>Edit permissions</strong></a>' % (reverse('admin:cors_origin_change', args=[instance.pk]))
                + self.permissions_list(instance)
            )
    edit_url.allow_tags = True


class InlineGroupAdmin(admin.StackedInline):
    model = models.Group
    filter_horizontal = ('submitters',)
    extra = 0


class InlineDataSetPermissionAdmin(admin.TabularInline):
    model = models.DataSetPermission
    extra = 0


class InlineDataIndexAdmin(admin.TabularInline):
    model = models.DataIndex
    extra = 0


class InlineWebhookAdmin(admin.StackedInline):
    model = models.Webhook
    extra = 0


class WebhookAdmin(admin.ModelAdmin):
    list_display = ('id', 'dataset', 'submission_set', 'event', 'url',)
    # list_filter = ('name',)


class DataSetAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'slug', 'owner')
    prepopulated_fields = {'slug': ['display_name']}
    search_fields = ('display_name', 'slug', 'owner__username')

    raw_id_fields = ('owner',)
    inlines = [InlineDataIndexAdmin, InlineDataSetPermissionAdmin, InlineApiKeyAdmin, InlineOriginAdmin, InlineGroupAdmin, InlineWebhookAdmin]

    def get_queryset(self, request):
        qs = super(DataSetAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(owner=user)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        # Hide the owner field from non-superusers. All objects visible to the
        # user should be assumed to be owned by themselves.
        if not request.user.is_superuser:
            self.exclude = (self.exclude or ()) + ('owner',)
        return super(DataSetAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        # Set the current user as the owner if the object has no owner and the
        # user is not a superuser.
        user = request.user
        if not user.is_superuser:
            if obj.owner_id is None:
                obj.owner = user
        super(DataSetAdmin, self).save_model(request, obj, form, change)


class PlaceAdmin(SubmittedThingAdmin):
    model = models.Place


class SubmissionSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_filter = ('name',)


class SubmissionAdmin(SubmittedThingAdmin):
    model = models.Submission

    list_display = SubmittedThingAdmin.list_display + ('place', 'set_',)
    list_filter = (SubmissionSetFilter,) + SubmittedThingAdmin.list_filter
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
    list_display = ('id', 'created_datetime', 'action', 'type_of_thing', 'submitter_name', 'source')

    # Pre-Django 1.6
    def queryset(self, request):
        qs = super(ActionAdmin, self).queryset(request)
        return qs.select_related('submitter', 'thing', 'thing__place')

    # Django 1.6+
    def get_queryset(self, request):
        qs = super(ActionAdmin, self).get_queryset(request)
        return qs.select_related('submitter', 'thing', 'thing__place')

    def submitter_name(self, obj):
        return obj.submitter.username if obj.submitter else None

    def type_of_thing(self, obj):
        if obj.thing.place:
            return 'place'
        else:
            return 'submission'


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


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = models.User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm

    fieldsets = BaseUserAdmin.fieldsets + (
            # (None, {'fields': ('some_extra_data',)}),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.DataSet, DataSetAdmin)
admin.site.register(models.Place, PlaceAdmin)
admin.site.register(models.SubmissionSet, SubmissionSetAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.Webhook, WebhookAdmin)
