from social_core.backends.base import BaseAuth
from social_core.backends.oauth import BaseOAuth2


class DynamicProviderModelAuth (BaseAuth):

    def authenticate(self, *args, **kwargs):
        backend = kwargs.get('backend')
        if (
            not hasattr(backend, 'model')
            or not hasattr(backend, 'name')
        ):
            return None

        self.name = backend.name
        return super().authenticate(*args, **kwargs)

