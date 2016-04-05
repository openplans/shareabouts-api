import base64
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from remote_client_user.middleware import get_authed_user
from remote_client_user.models import ClientPermissions
# from provider.constants import CONFIDENTIAL
# from provider.oauth2.models import Client
# replacing django-oauth2-provider with django-oauth-toolkit
from oauth2_provider.models import Application
# from oauth2_provider.models.Application import CLIENT_CONFIDENTIAL
from nose.tools import assert_is_none, assert_is_not_none


class RemoteClientUserTests (TestCase):
    def test_no_auth_with_blank_auth_header(self):
        request = RequestFactory().get('')
        request.META.pop('HTTP_AUTHORIZATION', None)

        auth = get_authed_user(request)
        assert_is_none(auth)

    def test_no_auth_with_non_remote_auth_header(self):
        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Basic abcdefg'

        auth = get_authed_user(request)
        assert_is_none(auth)

    def test_no_auth_with_invalid_remote_auth_header_data(self):
        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Remote ' + base64.encodestring('skittles').strip()

        auth = get_authed_user(request)
        assert_is_none(auth)

    def test_no_auth_with_nonexistant_client(self):
        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Remote ' + base64.encodestring('abc;123;mjumbewu;mjumbewu@example.com').strip()

        auth = get_authed_user(request)
        assert_is_none(auth)

    def test_no_auth_with_client_with_no_permissions(self):
        User = get_user_model()
        user = User.objects.create_user(username='mjumbewu', email='mjumbewu@example.com', password='!')
        
        Application.objects.create(client_id='abc', client_secret='123', user_id=user.id, client_type=Application.CLIENT_CONFIDENTIAL, redirect_uris='http://www.example.com')

        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Remote ' + base64.encodestring('abc;123;mjumbewu;mjumbewu@example.com').strip()

        auth = get_authed_user(request)
        assert_is_none(auth)

    def test_auth_with_client_with_login_permissions(self):
        User = get_user_model()
        user = User.objects.create_user(username='mjumbewu', email='mjumbewu@example.com', password='!')
        
        client = Application.objects.create(client_id='abc', client_secret='123', user_id=user.id, client_type=Application.CLIENT_CONFIDENTIAL, redirect_uris='http://www.example.com')
        ClientPermissions.objects.create(client=client, allow_remote_signin=True)

        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Remote ' + base64.encodestring('abc;123;mjumbewu;mjumbewu@example.com').strip()

        auth = get_authed_user(request)
        assert_is_not_none(auth)

    def test_no_auth_with_client_with_no_signup_permissions(self):
        User = get_user_model()
        user = User.objects.create_user(username='dvalpey', email='dvalpey@example.com', password='!')
        
        client = Application.objects.create(client_id='abc', client_secret='123', user_id=user.id, client_type=Application.CLIENT_CONFIDENTIAL, redirect_uris='http://www.example.com')
        ClientPermissions.objects.create(client=client, allow_remote_signin=True)

        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Remote ' + base64.encodestring('abc;123;mjumbewu;mjumbewu@example.com').strip()

        auth = get_authed_user(request)
        assert_is_none(auth)

    def test_auth_with_client_with_signup_permissions(self):
        User = get_user_model()
        user = User.objects.create_user(username='dvalpey', email='dvalpey@example.com', password='!')
        
        client = Application.objects.create(client_id='abc', client_secret='123', user_id=user.id, client_type=Application.CLIENT_CONFIDENTIAL, redirect_uris='http://www.example.com')
        ClientPermissions.objects.create(client=client, allow_remote_signin=True, allow_remote_signup=True)

        request = RequestFactory().get('')
        request.META['HTTP_AUTHORIZATION'] = 'Remote ' + base64.encodestring('abc;123;mjumbewu;mjumbewu@example.com').strip()

        auth = get_authed_user(request)
        assert_is_not_none(auth)
