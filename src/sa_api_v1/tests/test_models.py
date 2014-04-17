from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from djangorestframework.response import ErrorResponse
from mock import patch
from nose.tools import (istest, assert_equal, assert_not_equal, assert_in,
                        assert_raises)
from ..models import DataSet, Place, Submission, SubmissionSet
from ..models import SubmittedThing, Activity
from ..views import SubmissionCollectionView
from ..views import raise_error_if_not_authenticated
from ..views import ApiKeyCollectionView
from ..views import OwnerPasswordView
import json
import mock


User = get_user_model()


class TestSubmittedThingModel(TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        SubmittedThing.objects.all().delete()
        Activity.objects.all().delete()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)

    @istest
    def creates_activity_when_created_by_default(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save()
        qs = Activity.objects.all()
        self.assertEqual(qs.count(), 1)

    @istest
    def creates_activity_when_updated_by_default(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save()
        st.submitter_name = 'changed'
        st.save()
        qs = Activity.objects.all()
        self.assertEqual(qs.count(), 2)

    @istest
    def does_not_create_activity_when_silently_created(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save(silent=True)
        qs = Activity.objects.all()
        self.assertEqual(qs.count(), 0)

    @istest
    def does_not_create_activity_when_silently_updated(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save()
        st.submitter_name = 'changed'
        st.save(silent=True)
        qs = Activity.objects.all()
        self.assertEqual(qs.count(), 1)

