from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from .. import utils


class ShareaboutsUserManager (UserManager):
    def get_queryset(self):
        return super(ShareaboutsUserManager, self).get_queryset().prefetch_related('_groups')


class User (AbstractUser):
    objects = ShareaboutsUserManager()

    @utils.memo
    def get_groups(self):
        return self._groups.all().prefetch_related('permissions')

    class Meta:
        app_label = 'sa_api_v2'
        db_table = 'auth_user'


class Group (models.Model):
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


