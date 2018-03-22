import base64
import logging
from django.contrib.auth import get_user_model, SESSION_KEY, BACKEND_SESSION_KEY
# TODO: Update this to use django-oauth-toolkit; needed for the region service
# from provider.oauth2.models import Client
from remote_client_user.models import ClientPermissions
from rest_framework.authentication import get_authorization_header

logger = logging.getLogger('remote_client_user')


# TODO: Update this to use django-oauth-toolkit
def get_authed_user(request):
    # Get the HTTP Authorization header value
    auth_header = get_authorization_header(request).split()
    if not auth_header:
        return None

    if auth_header[0].lower() != 'remote':
        return None

    # Decode the base64-encoded header data
    encoded_auth_data = auth_header[1]
    auth_data = base64.decodestring(encoded_auth_data)

    # Parse out the client and user information
    try:
        client_id, client_secret, username, email = auth_data.split(';')
    except ValueError:
        return None

    # Get the client
    try:
        client = Client.objects.select_related('permissions').get(client_id=client_id, client_secret=client_secret)
    except Client.DoesNotExist:
        return None

    # Get or create the user if the client allows
    try:
        if not client.permissions.allow_remote_signin:
            return None
    except ClientPermissions.DoesNotExist:
        return None

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        if not client.permissions.allow_remote_signup:
            return None
        user = User.objects.create_user(username=username, email=email)
    return user


class RemoteClientMiddleware(object):
    def process_request(self, request):
        user = get_authed_user(request)

        # Set the current user ID and the appropriate authentication backend
        # on the session.
        if user:
            request.session[SESSION_KEY] = user.id
            request.session[BACKEND_SESSION_KEY] = 'sa_api_v2.auth_backends.CachedModelBackend'
