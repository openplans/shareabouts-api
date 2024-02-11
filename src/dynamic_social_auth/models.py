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
    # default_scope = models.TextField(help_text='''
    #     Some providers give nothing about the user but some basic data like the
    #     user Id or an email address. The default scope attribute is used to
    #     specify a default value for the scope argument to request those extra
    #     bits.
    # ''')
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

    class Meta:
        verbose_name = 'OAuth2 Provider'

    def __str__(self):
        return self.name

    def make_backend_class(self):
        class DynamicOAuth2 (BaseOAuth2):
            name = self.name

            ID_KEY = self.id_key
            REQUIRES_EMAIL_VALIDATION = self.requires_email_validation
            # EXTRA_DATA = self.extra_data
            SCOPE_PARAMETER_NAME = self.scope_parameter_name
            # DEFAULT_SCOPE = self.default_scope
            SCOPE_SEPARATOR = self.scope_separator
            AUTHORIZATION_URL = self.authorization_url
            ACCESS_TOKEN_URL = self.access_token_url
            ACCESS_TOKEN_METHOD = self.access_token_method
            REFRESH_TOKEN_URL = self.refresh_token_url
            REFRESH_TOKEN_METHOD = self.refresh_token_method
            REVOKE_TOKEN_URL = self.revoke_token_url
            REVOKE_TOKEN_METHOD = self.revoke_token_method
            RESPONSE_TYPE = self.response_type
            STATE_PARAMETER = self.state_parameter
            REDIRECT_STATE = self.redirect_state
            # USE_BASIC_AUTH = self.use_basic_auth

        return DynamicOAuth2
