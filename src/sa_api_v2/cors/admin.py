from django.contrib.admin import ModelAdmin
from django.contrib.gis import admin
from sa_api_v2.cors.models import OriginPermission


class OriginPermissionAdmin(ModelAdmin):
    list_display = ('pattern', 'dataset', 'logged_ip', 'last_used')

    def save_model(self, request, obj, form, change):
        if obj.logged_ip == '':
            obj.logged_ip = None
        super(OriginPermissionAdmin, self).save_model(request, obj, form, change)

admin.site.register(OriginPermission, OriginPermissionAdmin)
