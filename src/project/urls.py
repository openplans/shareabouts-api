from django.conf.urls import include
from django.conf import settings
from django.urls import path, re_path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import django.contrib.auth.views
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import resolve_url
import loginas.urls

admin.autodiscover()

urlpatterns = [
    # Examples:
    # re_path(r'^$', 'project.views.home', name='home'),
    # re_path(r'^project/', include('project.foo.urls')),

    # NOTE: Redirect all manager urls until the manager is fixed.
    re_path(r'^$', lambda x: HttpResponseRedirect(resolve_url(settings.ROOT_REDIRECT_TO))),

    # Uncomment the admin/doc line below to enable admin documentation:
    # re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    path(r'admin/', include(loginas.urls)),
    path(r'admin/', admin.site.urls),

    # For now, use basic auth.
    re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^accounts/logout/$', django.contrib.auth.views.logout_then_login,
        name='manager_logout'),

    # For now, the API and the management console are hosted together.
    re_path(r'^api/v2/', include('sa_api_v2.urls')),
    re_path(r'^api/v1/', lambda x: HttpResponse(status=410)),

]

# Debug toolbar explicit setup
from django.conf import settings
if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
