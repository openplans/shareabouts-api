from django.db import models


# Create your models here.
class ClientPermissions (models.Model):
    client = models.OneToOneField('oauth2.Client', related_name='permissions')
    allow_remote_signin = models.BooleanField(default=False)
    allow_remote_signup = models.BooleanField(default=False)

    def __unicode__(self):
        return self.client.url