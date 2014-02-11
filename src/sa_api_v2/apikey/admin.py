from django.contrib.admin import ModelAdmin
from django.contrib.gis import admin
from .. import models
from .models import ApiKey

from .forms import ApiKeyForm


class InlineKeyPermissionAdmin(admin.StackedInline):
    model = models.KeyPermission
    extra = 1


class ApiKeyAdmin(ModelAdmin):
    inlines = [InlineKeyPermissionAdmin]
    form = ApiKeyForm
    list_display = ('key', 'dataset', 'logged_ip', 'last_used')

admin.site.register(ApiKey, ApiKeyAdmin)
