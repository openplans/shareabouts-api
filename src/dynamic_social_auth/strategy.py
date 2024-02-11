from social_core.exceptions import MissingBackend
from social_django.strategy import DjangoStrategy
from .models import OAuth2Provider


class DjangoModelStrategy (DjangoStrategy):
    """
    To use this strategy add the following in the settings module:

    SOCIAL_AUTH_STRATEGY = 'dynamic_social_auth.strategy.DjangoModelStrategy'
    """
    def get_backend_class(self, name):
        try:
            # Try to get the backend using Django's default strategy
            return super().get_backend_class(name)

        except MissingBackend as missing_backend_exc:
            try:
                # If the default strategy fails, check whether we have a
                # dynamic provider definition
                provider = OAuth2Provider.objects.get(name=name)

            except OAuth2Provider.DoesNotExist:
                raise missing_backend_exc

            return provider.make_backend_class()
