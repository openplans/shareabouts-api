from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from .caching import CacheClearingModel
from .. import cache
from .. import utils
from ..models.mixins import CloneableModelMixin


class ShareaboutsUserManager (UserManager):
    def get_queryset(self):
        return super(ShareaboutsUserManager, self).get_queryset().prefetch_related('_groups')


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
    dataset = models.ForeignKey('DataSet', help_text='Which dataset does this group apply to?')
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
