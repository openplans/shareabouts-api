import re
from django.conf import settings
from django.contrib import auth
import dynamic_social_auth.models
import dynamic_social_auth.backends


DYNAMIC_PROVIDER_PATTERN = re.compile(r'dynamic_social_auth.models.(?P<backend_cls_name>\w+)')


def preload_dynamic_backend(backend_path):
    """
    Make a backend available at the given backend path if the user has already
    authenticated with a dynamic_social_auth backend. The backend does not have
    to be the one that authenticated the user -- it just has to be one that
    knows how to load a user model.
    """
    match = DYNAMIC_PROVIDER_PATTERN.match(backend_path)
    if match:
        backend_cls_name = match.group('backend_cls_name')
        try:
            getattr(
                dynamic_social_auth.models,
                backend_cls_name,
            )
        except AttributeError:
            setattr(
                dynamic_social_auth.models,
                backend_cls_name,
                dynamic_social_auth.backends.DynamicProviderModelAuth,
            )
        settings.AUTHENTICATION_BACKENDS = settings.AUTHENTICATION_BACKENDS + (backend_path,)


class DynamicSocialAuthMiddleware:
    """
    Middleware that simply ensures that a dynamic_social_auth backend is loaded
    when a user that is already logged in visits the site.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        backend_path = request.session.get(auth.BACKEND_SESSION_KEY)
        if backend_path:
            preload_dynamic_backend(backend_path)
        return self.get_response(request)