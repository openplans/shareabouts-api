from django.contrib.admin import ModelAdmin
from django.contrib import admin
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
    raw_id_fields = ['dataset']

    class Media:
        js = (
            'admin/js/jquery-1.11.0.min.js',
            'admin/js/jquery-ui-1.10.4.min.js',
            'admin/js/admin-list-reorder.js',
        )

    def get_queryset(self, request):
        qs = super(ApiKeyAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(dataset__owner=user)
        return qs

admin.site.register(ApiKey, ApiKeyAdmin)
