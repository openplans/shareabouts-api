from django.test import TestCase
# from django.test.client import Client
# from django.test.client import RequestFactory
# from django.contrib.auth.models import User
from django.core.cache import cache
# from django.core.urlresolvers import reverse
# from djangorestframework.response import ErrorResponse
# from mock import patch
# from nose.tools import (istest, assert_equal, assert_not_equal, assert_in,
#                         assert_raises)
from ..models import DataSet, User, SubmittedThing, Action, Place
# from ..views import SubmissionCollectionView
# from ..views import raise_error_if_not_authenticated
# from ..views import ApiKeyCollectionView
# from ..views import OwnerPasswordView
# import json
import mock


class TestSubmittedThing (TestCase):
    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        SubmittedThing.objects.all().delete()
        Action.objects.all().delete()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)

    def test_save_creates_action_by_default(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save()
        qs = Action.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].thing_id, st.id)

    def test_save_creates_action_when_updated_by_default(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save()
        st.data = '{"key": "value"}'
        st.save()
        qs = Action.objects.all()
        self.assertEqual(qs.count(), 2)

    def test_save_does_not_create_action_when_silently_created(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save(silent=True)
        qs = Action.objects.all()
        self.assertEqual(qs.count(), 0)

    def test_save_does_not_create_action_when_silently_updated(self):
        st = SubmittedThing(dataset=self.dataset)
        st.save()
        st.submitter_name = 'changed'
        st.save(silent=True)
        qs = Action.objects.all()
        self.assertEqual(qs.count(), 1)


class TestCacheClearingModel (TestCase):
    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Action.objects.all().delete()
        cache.clear()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)

    def test_v2_change_clears_v1_cache(self):
        place = Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')

        from sa_api_v1.models import Place as V1Place
        # Populate the cache initially
        mockgetter = mock.Mock(return_value=place)
        V1Place.cache.get_cached_instance_params(place.pk, mockgetter)
        self.assertEqual(mockgetter.call_count, 1)

        # Assert that there's no reason to get the actual place
        # (because all the required information should be cached)
        mockgetter = mock.Mock(return_value=place)
        V1Place.cache.get_cached_instance_params(place.pk, mockgetter)
        self.assertEqual(mockgetter.call_count, 0)

        # Invalidate the cache from the v2 object
        place.clear_instance_cache()

        # Now the cached info should be gone again
        mockgetter = mock.Mock(return_value=place)
        V1Place.cache.get_cached_instance_params(place.pk, mockgetter)
        self.assertEqual(mockgetter.call_count, 1)

    def test_v1_cache_ignores_non_points(self):
        place = Place.objects.create(dataset=self.dataset, geometry='LINESTRING(0 0, 1 1)')

        with mock.patch('sa_api_v1.models.Place.cache.clear_instance') as mockclear:
            place.clear_instance_cache()

            # Now the cached info should be gone again
            self.assertEqual(mockclear.call_count, 0)

