import base64
from django.contrib.auth import get_user_model
from provider.oauth2.models import Client
from remote_client_user.models import ClientPermissions
from rest_framework import HTTP_HEADER_ENCODING

def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if type(auth) == type(''):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


class RemoteClientBackend(object):
    """
    Backend that tries to authenticate a user based on information passed from
    a client with sufficient permissions.
    """
    def authenticate(self, request=None):
        if request is None:
            return None

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


