"""
REST API Key model implementation derived from django-apikey,
copyright (c) 2011 Steve Scoursen and Jorge Eduardo Cardona.
BSD license.
http://pypi.python.org/pypi/django-apikey

Key generation derived from
http://jetfar.com/simple-api-key-generation-in-python/
license unknown.
"""

from django.db import models
from django.db.models.signals import post_save
from django.utils.timezone import now
from ..models import DataSet, KeyPermission
from ..models.mixins import CloneableModelMixin
from .. import utils

# Changing this would require a migration, ugh.
KEY_SIZE = 32


def generate_unique_api_key():
    """random string suitable for use with ApiKey.

    Algorithm from http://jetfar.com/simple-api-key-generation-in-python/
    """
    import base64
    import hashlib
    import random
    api_key = ''
    while len(api_key) < KEY_SIZE:
        more_key = str(random.getrandbits(256)).encode()
        more_key = hashlib.sha256(more_key).hexdigest().encode()
        more_key = base64.b64encode(
            more_key,
            random.choice(['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD']).encode())
        more_key = more_key.decode().rstrip('=')
        api_key += more_key
    api_key = api_key[:KEY_SIZE]
    return api_key


class ApiKey(CloneableModelMixin, models.Model):
    key = models.CharField(max_length=KEY_SIZE, unique=True, default=generate_unique_api_key)
    logged_ip = models.GenericIPAddressField(blank=True, null=True)
    last_used = models.DateTimeField(blank=True, default=now)
    dataset = models.ForeignKey(DataSet, on_delete=models.CASCADE, blank=True, related_name='keys')

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'apikey_apikey'

    def login(self, ip_address):
        self.logged_ip = ip_address
        self.save()

    def logout(self):
        # YAGNI?
        self.logged_ip = None
        self.save()

    @property
    def owner(self):
        try:
            return self.dataset.owner
        except AttributeError:
            return None

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.key

    def clone_related(self, onto):
        for permission in self.permissions.all():
            permission.clone(overrides={'key': onto})

    def get_ignore_fields(self, ModelClass):
        fields = super(ApiKey, self).get_ignore_fields(ModelClass)
        # Do not copy over the actual key value
        if ModelClass == ApiKey:
            fields.add('key')
        return fields

    def save(self, *args, **kwargs):
        if self.logged_ip == '':
            self.logged_ip = None
        return super(ApiKey, self).save(*args, **kwargs)


def create_data_permissions(sender, instance, created, **kwargs):
    """
    Create a default permission instance for a new API key.
    """
    if created:
        KeyPermission.objects.create(key=instance, submission_set='*',
            can_retrieve=True, can_create=True, can_update=True, can_destroy=True)
post_save.connect(create_data_permissions, sender=ApiKey, dispatch_uid="apikey-create-permissions")
