from django.contrib import admin
from remote_client_user.models import ClientPermissions


class ClientPermissionsAdmin (admin.ModelAdmin):
    raw_id_fields = ('client',)


# Register your models here.
admin.site.register(ClientPermissions, ClientPermissionsAdmin)