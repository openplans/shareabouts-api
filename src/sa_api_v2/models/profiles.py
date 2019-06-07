from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from .caching import CacheClearingModel
from .. import cache
from .. import utils
from ..models.mixins import CloneableModelMixin


class ShareaboutsUserManager (UserManager):
    def get_queryset(self):
        return super(ShareaboutsUserManager, self).get_queryset().prefetch_related('_groups')

    def get_twitter_access_token(self):
        from django.conf import settings
        import requests

        key = settings.SOCIAL_AUTH_TWITTER_KEY
        secret = settings.SOCIAL_AUTH_TWITTER_SECRET

        auth_url = 'https://api.twitter.com/oauth2/token'
        token_response = requests.post(auth_url,
            auth=(key, secret), data={'grant_type': 'client_credentials'})

        if token_response.status_code != 200:
            raise Exception('Received a {0} response while retrieving Twitter '
                'authorization token: "{1}"'.format(
                token_response.status_code, token_response.text))

        access_token = token_response.json().get('access_token')
        return access_token

    def ensure_social_user(self, provider, user_id, username, extra_data=None, firstname=None, lastname=None):
        from social.apps.django_app.default.models import UserSocialAuth
        import uuid

        try:
            social_auth = UserSocialAuth.objects.get(
                provider=provider,
                uid=user_id)
            user = social_auth.user

        except UserSocialAuth.DoesNotExist:
            internal_username = username
            while User.objects.filter(username=internal_username).exists():
                internal_username = username + uuid.uuid4().hex[:16]

            user = User.objects.create(
                username=internal_username,
                first_name=firstname or '',
                last_name=lastname or '')

            social_auth = UserSocialAuth(
                user=user,
                provider=provider,
                uid=user_id,
                extra_data=extra_data or {}
            )
            social_auth.save()

        return user, social_auth

    def add_twitter_user(self, username, firstname=None, lastname=None):
        import requests
        access_token = self.get_twitter_access_token()

        user_tpl = 'https://api.twitter.com/1.1/users/show.json?screen_name={}'
        user_url = user_tpl.format(username)

        headers = {'Authorization': 'Bearer ' + access_token}
        response = requests.get(user_url, headers=headers)

        if response.status_code != 200:
            raise Exception('Received a {0} response while trying to get user '
                'details for user "{2}" from twitter: {1}'.format(
                    response.status_code, response.text, username))

        user_data = response.json()
        user_id = user_data['id']
        social_data = {
            'access_token': {
                'screen_name': username,
                'oauth_token': 'temp-fake-token',          # replaced on login
                'oauth_token_secret': 'temp-fake-secret',  # replaced on login
                'user_id': str(user_id)
            },
            'id': user_id,
            'name': user_data.get('name'),
            'profile_image_url': user_data.get('profile_image_url_https'),
        }

        return self.ensure_social_user('twitter', user_id, username, social_data, firstname, lastname)

    def add_third_party_user(self, provider, username, firstname, lastname):
        if provider == 'twitter':
            return self.add_twitter_user(username, firstname, lastname)
        else:
            raise NotImplemented('Adding by {0} is not yet implemented'.format(provider))


class User (CacheClearingModel, AbstractUser):
    objects = ShareaboutsUserManager()
    cache = cache.UserCache()

    @utils.memo
    def get_groups(self):
        return self._groups.all().prefetch_related('permissions')

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'auth_user'


class Group (CloneableModelMixin, models.Model):
    """
    A group of submitters within a dataset.
    """
    dataset = models.ForeignKey('DataSet', on_delete=models.CASCADE, help_text='Which dataset does this group apply to?', related_name='groups')
    name = models.CharField(max_length=32, help_text='What is the name of the group to which users with this group belong? For example: "judges", "administrators", "winners", ...')
    submitters = models.ManyToManyField(User, related_name='_groups', blank=True)

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'sa_api_group'
        unique_together = [('name', 'dataset')]

    def __unicode__(self):
        return '%s in %s' % (self.name, self.dataset.slug)

    def clone_related(self, onto):
        for permission in self.permissions.all():
            permission.clone(overrides={'group': onto})

        for submitter in self.submitters.all():
            onto.submitters.add(submitter)
