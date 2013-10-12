from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from rest_framework import authentication
from sa_api_v2.cors.models import OriginPermission


# Client authentication with CORS
class OriginAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        """
        Return a Client, or something usable as such, if the origin has
        permission to access the dataset;
        as per http://django-rest-framework.org/library/authentication.html
        """

        dataset = request.get_dataset()
        origin = request.META.get('HTTP_ORIGIN', '')

        try:
            client, auth = self.check_origin_permission(origin, dataset)
        except PermissionDenied:
            return None

        return (client, auth)

    def check_origin_permission(self, origin, dataset):
        for perm in dataset.origin_permissions.all():
            if OriginPermission.match(perm.pattern, origin):
                return perm, perm
        raise PermissionDenied("None of the dataset's origin permission policies matched")
