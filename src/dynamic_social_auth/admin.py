from django.contrib import admin
from .models import OAuth2Provider


class OAuth2ProviderAdmin (admin.ModelAdmin):
    list_display = ['name', 'description']


admin.site.register(OAuth2Provider, OAuth2ProviderAdmin)
