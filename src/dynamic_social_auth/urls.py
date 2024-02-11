from django.conf.urls import include
from django.urls import path
import social_django.urls


urlpatterns = [
    path('', include(social_django.urls, namespace='social')),
]
