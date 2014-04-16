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
import re


class Origin(models.Model):
    pattern = models.CharField(max_length=100, help_text='The origin pattern, e.g., *.github.com, localhost:*, map.phila.gov')
    logged_ip = models.IPAddressField(blank=True, null=True)
    last_used = models.DateTimeField(blank=True, default=now)

    # I think we are going to only have one key per dataset,
    # but that could change on either end.
    datasets = models.ManyToManyField(DataSet, blank=True,
                                      related_name='origins')

    class Meta:
        db_table = 'cors_origin'

    def login(self, ip_address):
        self.logged_ip = ip_address
        self.save()

    def logout(self):
        # YAGNI?
        self.logged_ip = None
        self.save()

    @property
    def dataset(self):
        try:
            return self.datasets.all()[0]
        except IndexError:
            return None

    @property
    def owner(self):
        try:
            return self.dataset.owner
        except AttributeError:
            return None

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

        # No wild-cards; literal
        elif '*' not in pattern:
            return pattern == origin

        # Wildcards; convert to regex
        else:
            pattern = pattern.replace('.', r'\.').replace('*', r'.*')
            return re.match(pattern, origin) is not None


def create_data_permissions(sender, instance, created, **kwargs):
    """
    Create a default permission instance for a new origin.
    """
    if created:
        OriginPermission.objects.create(origin=instance, submission_set='*',
            can_retrieve=True, can_create=True, can_update=True, can_destroy=True)
post_save.connect(create_data_permissions, sender=Origin, dispatch_uid="origin-create-permissions")
