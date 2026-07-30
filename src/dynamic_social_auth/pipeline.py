from social_core.pipeline.user import get_username as default_get_username


def get_username(strategy, details, backend, user=None, *args, **kwargs):
    """
    Pipeline step that prefixes usernames with the social auth backend's provider
    name (e.g. 'provider-name:username') before delegating to the standard
    get_username step for collision resolution and cleaning.
    """
    if not user:
        raw_username = details.get('username')
        if not raw_username:
            if strategy.setting('USERNAME_IS_FULL_EMAIL', False) and details.get('email'):
                raw_username = details['email']
            elif details.get('email'):
                raw_username = details['email'].split('@', 1)[0]
            else:
                from uuid import uuid4
                raw_username = uuid4().hex

        prefixed_username = f'{backend.name}:{raw_username}'

        details = details.copy()
        details['username'] = prefixed_username

    return default_get_username(strategy, details, backend, user=user, *args, **kwargs)
