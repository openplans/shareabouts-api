from django.contrib.admin import ModelAdmin
from django.contrib import admin
from .. import models
from sa_api_v2.cors.models import Origin


class InlineOriginPermissionAdmin(admin.TabularInline):
    model = models.OriginPermission
    extra = 0


class OriginAdmin(ModelAdmin):
    inlines = [InlineOriginPermissionAdmin]
    list_display = ('pattern', 'dataset', 'logged_ip', 'last_used')
    raw_id_fields = ['dataset']

    class Media:
        js = (
            'admin/js/jquery-1.11.0.min.js',
            'admin/js/jquery-ui-1.10.4.min.js',
            'admin/js/admin-list-reorder.js',
        )

    def get_queryset(self, request):
        qs = super(OriginAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(dataset__owner=user)
        return qs

    def save_model(self, request, obj, form, change):
        if obj.logged_ip == '':
            obj.logged_ip = None
        super(OriginAdmin, self).save_model(request, obj, form, change)

admin.site.register(Origin, OriginAdmin)
