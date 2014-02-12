from django.contrib.admin import ModelAdmin
from django.contrib.gis import admin
from .. import models
from .models import ApiKey

from .forms import ApiKeyForm


class InlineKeyPermissionAdmin(admin.TabularInline):
    model = models.KeyPermission
    extra = 0


class ApiKeyAdmin(ModelAdmin):
    inlines = [InlineKeyPermissionAdmin]
    form = ApiKeyForm
    list_display = ('key', 'dataset', 'logged_ip', 'last_used')

    class Media:
        js = (
            'admin/js/jquery-1.11.0.min.js',
            'admin/js/jquery-ui-1.10.4.min.js',
            'admin/js/admin-list-reorder.js',
        )

admin.site.register(ApiKey, ApiKeyAdmin)
