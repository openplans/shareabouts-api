from django.db import models
from social_core.backends.oauth import BaseOAuth2


class OAuth2Provider (models.Model):
    """
    An OAuth2Provider can be used to specify an authentication authority for a
    given dataset. The fields, descriptions, and defaults listed herein are
    derived from the attributes of a social-auth OAuth2 backend, documented at
    https://python-social-auth.readthedocs.io/en/latest/backends/implementation.html#oauth
    """
    name = models.CharField(max_length=32, unique=True, help_text='''
        This defines the provider name and identifies it during the auth
        process.
    ''')
    description = models.TextField(default='', blank=True, help_text='''
        Describes the provider for documentation purposes. This field has no
        impact on the behavior of the provider.
    ''')
    id_key = models.CharField(default='id', help_text='''
        The default key name where the user identification field is defined,
        it’s used in the auth process when some basic user data is returned.
    ''')
    username_key = models.CharField(default='username', help_text='''
        The default key name where the user name field is defined, it’s used in
        the auth process when some basic user data is returned.
    ''')
    fullname_key = models.CharField(default='fullname', help_text='''
        The default key name where the user's full name field is defined, it’s
        primarily used for display purposes.
    ''')
    requires_email_validation = models.BooleanField(default=False, help_text='''
        Flags the backend to enforce email validation during the pipeline.
    ''')
    scope_parameter_name = models.CharField(default='scope', help_text='''
        The scope argument is used to tell the provider the API endpoints you
        want to call later, it’s a permissions request granted over the
        `access_token` later retrieved. The default value is `scope` since
        that’s usually the name used in the URL parameter, but can be
        overridden if needed.
    ''')
    default_scope = models.TextField(default='', blank=True, help_text='''
        Some providers give nothing about the user but some basic data like the
        user Id or an email address. The default scope attribute is used to
        specify a default value for the scope argument to request those extra
        bits. Should be a string using the `scope_separator` to distinguish
        between scopes.
    ''')
    scope_separator = models.CharField(default=' ', blank=True, max_length=10, help_text='''
        The scope argument is usually a list of permissions to request, the
        list is joined with a separator, usually just a blank space, but this
        can differ from provider to provider. Override the default value with
        this attribute if it differs.
    ''')
    authorization_url = models.URLField(help_text='''
        This is the entry point for the authorization mechanism, users must be
        redirected to this URL.
    ''')
    access_token_url = models.URLField(help_text='''
        Must point to the API endpoint that provides an `access_token` needed
        to authenticate in users behalf on future API calls.
    ''')
    use_basic_auth = models.BooleanField(default=False, help_text='''
        If true, will include the client_id and client_secret as the
        username/password when requesting the authorization token for a user.
    ''')
    access_token_method = models.CharField(default='GET', max_length=10, help_text='''
        Specifying the method type required to retrieve your access token if
        it’s not the default GET request.
    ''')
    refresh_token_url = models.URLField(null=True, blank=True, help_text='''
        Some providers give the option to renew the `access_token` since they
        are usually limited in time, once that time runs out, the token is
        invalidated and cannot be used anymore. This attribute should point to
        that API endpoint.
    ''')
    refresh_token_method = models.CharField(default='POST', max_length=10)
    revoke_token_url = models.URLField(null=True, blank=True)
    revoke_token_method = models.CharField(default='POST', max_length=10)
    response_type = models.CharField(default='code', help_text='''
        The response type expected on the auth process, default value is `code`
        as dictated by OAuth2 definition. Override it if default value doesn’t
        fit the provider implementation.
    ''')
    state_parameter = models.BooleanField(default=True, help_text='''
        OAuth2 defines that a state parameter can be passed in order to
        validate the process, it’s kind of a CSRF check to avoid man in the
        middle attacks. Some don’t recognise it or don’t return it which will
        make the auth process invalid. Set this attribute to `False` in that
        case.
    ''')
    redirect_state = models.BooleanField(default=False, help_text='''
        For those providers that don’t recognise the `state` parameter, the app
        can add a redirect_state argument to the `redirect_uri` to mimic it.
        Set this value to `False` if the provider likes to verify the
        `redirect_uri` value and this parameter invalidates that check.
    ''')
    user_data_url = models.URLField(null=True, blank=True, help_text='''
        URL to load user data from, after the access token is retrieved.
    ''')
    use_auth_header_for_user_data = models.BooleanField(default=True, help_text='''
        After auth token is retrieved, if `use_auth_header_for_user_data` is
        True, and `user_data_url` is specified, then retrieve user data from
        the URL, putting the access token in an Authorization header
    ''')
    auth_header_prefix = models.CharField(max_length=16, default='bearer', help_text='''
        The prefix for the `Authorization` header when retrieving user data.
        This field is only used if `user_data_url` is specified, and
        `use_auth_header_for_user_data` is True.
    ''')
    use_querystring_for_user_data = models.BooleanField(default=False, help_text='''
        After auth token is retrieved, if `use_querystring_for_user_data` is
        True, and `user_data_url` is specified, then retrieve user data from
        the URL, putting the access token in the query string.
    ''')
    access_token_param = models.CharField(max_length=32, default='access_token', help_text='''
        The query string key for the `access_token` parameter when retrieving
        user data. This field is only used if `user_data_url` is specified, and
        `use_querystring_for_user_data` is True.
    ''')

    class Meta:
        verbose_name = 'OAuth2 Provider'

    def __str__(self):
        return self.name

    def make_backend_class(self):
        model_instance = self

        class DynamicOAuth2 (BaseOAuth2):
            model = self.__class__
            name = model_instance.name

            ID_KEY = model_instance.id_key
            REQUIRES_EMAIL_VALIDATION = model_instance.requires_email_validation
            # EXTRA_DATA = model_instance.extra_data
            SCOPE_PARAMETER_NAME = model_instance.scope_parameter_name
            DEFAULT_SCOPE = (
                model_instance.default_scope.split(model_instance.scope_separator)
                if model_instance.default_scope
                else []
            )
            SCOPE_SEPARATOR = model_instance.scope_separator
            AUTHORIZATION_URL = model_instance.authorization_url
            ACCESS_TOKEN_URL = model_instance.access_token_url
            ACCESS_TOKEN_METHOD = model_instance.access_token_method
            REFRESH_TOKEN_URL = model_instance.refresh_token_url
            REFRESH_TOKEN_METHOD = model_instance.refresh_token_method
            REVOKE_TOKEN_URL = model_instance.revoke_token_url
            REVOKE_TOKEN_METHOD = model_instance.revoke_token_method
            RESPONSE_TYPE = model_instance.response_type
            STATE_PARAMETER = model_instance.state_parameter
            REDIRECT_STATE = model_instance.redirect_state
            USE_BASIC_AUTH = model_instance.use_basic_auth

            def get_request_data(self):
                # Python-social-auth attaches the strategy to a backend on
                # creation:
                # https://github.com/python-social-auth/social-core/blob/4bb29b1eaa60cb0288606c703e7e9aeea2a8184d/social_core/strategy.py#L176-L177
                strategy = self.strategy

                # The request_data function is defined in the DjangoStrategy
                # class:
                # https://github.com/python-social-auth/social-app-django/blob/4047ba4b3a3df887d395263a25fef17bcb21e60d/social_django/strategy.py#L48
                request_data = strategy.request_data()

                return request_data

            def get_redirect_uri(self, state=None):
                request_data = self.get_request_data()
                self.redirect_uri = request_data.get('redirect_uri')
                return super().get_redirect_uri(state)

            def get_key_and_secret(self):
                client_id, client_secret = super().get_key_and_secret()

                if client_id is None or client_secret is None:
                    request_data = self.get_request_data()
                    client_id = client_id or request_data.get('client_id')
                    client_secret = client_secret or request_data.get('client_secret')

                return client_id, client_secret

            def get_user_id(self, details, response):
                return super().get_user_id(details, response)

            def get_user_details(self, response):
                details = {
                    'username': response.get(model_instance.username_key),
                    'fullname': response.get(model_instance.fullname_key),
                }
                return details

            def user_data(self, access_token, *args, **kwargs):
                url = model_instance.user_data_url
                if not url:
                    return super().user_data(access_token, *args, **kwargs)

                headers = {}
                params = {}

                if model_instance.use_auth_header_for_user_data:
                    headers['Authorization'] = f'{model_instance.auth_header_prefix} {access_token}'
                if model_instance.use_querystring_for_user_data:
                    params[model_instance.access_token_param] = access_token

                breakpoint()
                return self.get_json(url, headers=headers, data=params)

        return DynamicOAuth2
