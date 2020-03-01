"""
Basic behind-the-scenes maintenance for superusers,
via django.contrib.admin.
"""

import itertools
import json
from django.conf import settings
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
if settings.USE_GEODB:
    from django.contrib.gis import admin
else:
    from django.contrib import admin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms import ValidationError, ModelForm
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django_ace import AceWidget
from django_object_actions import DjangoObjectActions
from . import models
from .apikey.models import ApiKey
from .cors.models import Origin
from .tasks import clone_related_dataset_data


class SubmissionSetFilter (SimpleListFilter):
    """
    Used to filter a list of submissions by type (set name).
    """
    title = 'Submission Set'
    parameter_name = 'set'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        qs = qs.order_by('set_name').distinct('set_name').values('set_name')
        return [(elem['set_name'], elem['set_name']) for elem in qs]

    def queryset(self, request, qs):
        set_name = self.value()
        if set_name:
            qs = qs.filter(set_name=set_name)
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


BaseGeoAdmin = admin.OSMGeoAdmin if settings.USE_GEODB else admin.ModelAdmin
class SubmittedThingAdmin(BaseGeoAdmin):
    date_hierarchy = 'created_datetime'
    inlines = (InlineAttachmentAdmin,)
    list_display = ('id', 'created_datetime', 'submitter_name', 'dataset', 'visible', 'data')
    list_editable = ('visible',)
    list_filter = (DataSetFilter,)
    search_fields = ('submitter__username', 'data',)

    openlayers_url = 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.13.1/OpenLayers.js'
    raw_id_fields = ('submitter', 'dataset')
    readonly_fields = ('api_path',)

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


class AlwaysChangedModelForm (ModelForm):
    def has_changed(self):
        """ Should returns True if data differs from initial.
        By always returning true even unchanged inlines will get validated and saved."""
        return True


class InlineApiKeyAdmin(admin.StackedInline):
    model = ApiKey
    form = AlwaysChangedModelForm
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
                '<a href="%s"><strong>Edit permissions</strong></a>' % (reverse('admin:sa_api_v2_apikey_change', args=[instance.pk]))
                + self.permissions_list(instance)
            )
    edit_url.allow_tags = True


class InlineOriginAdmin(admin.StackedInline):
    model = Origin
    form = AlwaysChangedModelForm
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
                '<a href="%s"><strong>Edit permissions</strong></a>' % (reverse('admin:sa_api_v2_origin_change', args=[instance.pk]))
                + self.permissions_list(instance)
            )
    edit_url.allow_tags = True


class InlineGroupAdmin(admin.StackedInline):
    model = models.Group
    filter_horizontal = ('submitters',)
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
                '<a href="%s"><strong>Edit permissions</strong></a>' % (reverse('admin:sa_api_v2_group_change', args=[instance.pk]))
                + self.permissions_list(instance)
            )
    edit_url.allow_tags = True


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
    raw_id_fields = ('dataset',)
    # list_filter = ('name',)

    def get_queryset(self, request):
        qs = super(WebhookAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(dataset__owner=user)
        return qs



class DataSetAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('display_name', 'slug', 'owner')
    prepopulated_fields = {'slug': ['display_name']}
    search_fields = ('display_name', 'slug', 'owner__username')

    objectactions = ('clone_dataset', 'clear_cache')
    raw_id_fields = ('owner',)
    readonly_fields = ('api_path','places')
    inlines = [InlineDataIndexAdmin, InlineDataSetPermissionAdmin, InlineApiKeyAdmin, InlineOriginAdmin, InlineGroupAdmin, InlineWebhookAdmin]

    def clear_cache(self, request, obj):
        obj.clear_instance_cache()

    def clone_dataset(self, request, obj):
        siblings = models.DataSet.objects.filter(owner=obj.owner)
        slugs = set([ds.slug for ds in siblings])

        for uniquifier in itertools.count(2):
            unique_slug = '-'.join([obj.slug, str(uniquifier)])
            if unique_slug not in slugs: break

        try:
            new_obj = obj.clone(overrides={'slug': unique_slug}, commit=False)
            new_obj.save()
            clone_related_dataset_data.apply_async(args=[obj.id, new_obj.id])

            new_obj_edit_url = reverse('admin:sa_api_v2_dataset_change', args=[new_obj.pk])
            messages.success(request, 'Cloning dataset. Please give it a few moments.')
            return HttpResponseRedirect(new_obj_edit_url)
        except Exception as e:
            messages.error(request, 'Failed to clone dataset: %s (%s)' % (e, type(e).__name__))

    def places(self, instance):
        path = '/admin/sa_api_v2/place/?dataset={}'
        path = path.format(instance.slug)
        return '<a href="{0}">{0}</a>'.format(path)
    places.allow_tags = True

    def api_path(self, instance):
        path = reverse('dataset-detail', args=[instance.owner, instance.slug])
        return '<a href="{0}">{0}</a>'.format(path)
    api_path.allow_tags = True

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

    def api_path(self, instance):
        path = reverse('place-detail', args=[instance.dataset.owner, instance.dataset.slug, instance.id])
        return '<a href="{0}">{0}</a>'.format(path)
    api_path.allow_tags = True


class SubmissionAdmin(SubmittedThingAdmin):
    model = models.Submission

    list_display = SubmittedThingAdmin.list_display + ('place', 'set_',)
    list_filter = (SubmissionSetFilter,) + SubmittedThingAdmin.list_filter
    search_fields = ('set_name',) + SubmittedThingAdmin.search_fields

    raw_id_fields = ('submitter', 'dataset', 'place')

    def set_(self, obj):
        return obj.set_name
    set_.short_description = 'Set'
    set_.admin_order_field = 'set_name'

    def place(self, obj):
        return obj.place_id
    place.admin_order_field = 'place'

    def api_path(self, instance):
        path = reverse('submission-detail', args=[instance.dataset.owner, instance.dataset.slug, instance.place.id, instance.set_name, instance.id])
        return '<a href="{0}">{0}</a>'.format(path)
    api_path.allow_tags = True


class ActionAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_datetime'
    list_display = ('id', 'created_datetime', 'action', 'type_of_thing', 'submitter_name', 'source')
    raw_id_fields = ('thing',)

    # Pre-Django 1.6
    def queryset(self, request):
        qs = super(ActionAdmin, self).queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(thing__dataset__owner=user)
        return qs.select_related('submitter', 'thing', 'thing__place')

    # Django 1.6+
    def get_queryset(self, request):
        qs = super(ActionAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(thing__dataset__owner=user)
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

    def get_queryset(self, request):
        qs = super(GroupAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(dataset__owner=user)
        return qs


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = models.User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    change_form_template = 'loginas/change_form.html'

    fieldsets = BaseUserAdmin.fieldsets + (
            # (None, {'fields': ('some_extra_data',)}),
    )

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            # Only show users that have contributed to the owner's datasets
            qs = qs.filter(things__dataset__owner=user)
        return qs


admin.site.register(models.User, UserAdmin)
admin.site.register(models.DataSet, DataSetAdmin)
admin.site.register(models.Place, PlaceAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.Webhook, WebhookAdmin)

admin.site.site_header = 'Shareabouts API Server Administration'
admin.site.site_title = 'Shareabouts API Server'
