from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from rest_framework import authentication
from sa_api_v2.cors.models import Origin


# Client authentication with CORS
class OriginAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        """
        Return a Client, or something usable as such, if the origin has
        permission to access the dataset;
        as per http://django-rest-framework.org/library/authentication.html
        """
        origin = request.META.get('HTTP_ORIGIN', '')

        if not origin:
            return None

        dataset = request.get_dataset()
        try:
            client, auth = self.check_origin_permission(origin, dataset)
        except PermissionDenied:
            return None

        return (client, auth)

    def check_origin_permission(self, origin_header, dataset):
        ds_origin = dataset.get_origin(origin_header)
        if ds_origin is not None:
            return ds_origin, ds_origin
        else:
            raise PermissionDenied("None of the dataset's origin permission policies matched")
