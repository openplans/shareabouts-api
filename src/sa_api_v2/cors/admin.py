from django.contrib.admin import ModelAdmin
from django.contrib.gis import admin
from sa_api_v2.cors.models import OriginPermission


class OriginPermissionAdmin(ModelAdmin):
    list_display = ('pattern', 'dataset', 'logged_ip', 'last_used')

admin.site.register(OriginPermission, OriginPermissionAdmin)
