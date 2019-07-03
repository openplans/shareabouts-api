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
from ..models import DataSet, OriginPermission
from ..models.mixins import CloneableModelMixin
from .. import utils
import re


class Origin(CloneableModelMixin, models.Model):
    pattern = models.CharField(max_length=100, help_text='The origin pattern, e.g., https://*.github.io, http://localhost:*, http*://map.phila.gov')
    logged_ip = models.GenericIPAddressField(blank=True, null=True)
    last_used = models.DateTimeField(blank=True, default=now)
    dataset = models.ForeignKey(DataSet, on_delete=models.CASCADE, blank=True, related_name='origins')

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'cors_origin'

    def login(self, ip_address):
        self.logged_ip = ip_address
        self.save()

    def logout(self):
        # YAGNI?
        self.logged_ip = None
        self.save()

    # @property
    # def dataset(self):
    #     try:
    #         return self.datasets.all()[0]
    #     except IndexError:
    #         return None

    @property
    def owner(self):
        try:
            return self.dataset.owner
        except AttributeError:
            return None

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.pattern

    @staticmethod
    def match(pattern, origin):
        """
        Determine whether a given origin matches an origin pattern.
        """
        # Universal
        if pattern == '*':
            return True

        # No scheme specified; assume all HTTP[S]
        if '://' not in pattern:
            pattern = 'http*://' + pattern

        # No wild-cards; literal
        if '*' not in pattern:
            return pattern == origin

        # Wildcards; convert to regex
        else:
            pattern = pattern.replace('.', r'\.').replace('*', r'.*')
            return re.match(pattern, origin) is not None

    def clone_related(self, onto):
        for permission in self.permissions.all():
            permission.clone(overrides={'origin': onto})

    def save(self, *args, **kwargs):
        if self.logged_ip == '':
            self.logged_ip = None
        return super(Origin, self).save(*args, **kwargs)


def create_data_permissions(sender, instance, created, **kwargs):
    """
    Create a default permission instance for a new origin.
    """
    if created:
        OriginPermission.objects.create(origin=instance, submission_set='*',
            can_retrieve=True, can_create=True, can_update=True, can_destroy=True)
post_save.connect(create_data_permissions, sender=Origin, dispatch_uid="origin-create-permissions")
