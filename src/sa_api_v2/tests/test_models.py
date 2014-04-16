from django.test import TestCase
# from django.test.client import Client
from django.test.client import RequestFactory
# from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
# from djangorestframework.response import ErrorResponse
# from mock import patch
# from nose.tools import (istest, assert_equal, assert_not_equal, assert_in,
#                         assert_raises)
from ..models import DataSet, User, SubmittedThing, Action, Place, SubmissionSet, Submission, check_data_permission
from ..apikey.models import ApiKey
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
        SubmissionSet.objects.all().delete()
        Submission.objects.all().delete()
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

    def test_saving_submission_on_non_point_place_is_happy(self):
        place = Place.objects.create(dataset=self.dataset, geometry='LINESTRING(0 0, 1 1)')
        sset = SubmissionSet.objects.create(place=place, name='doesnt-matter')
        submission = Submission.objects.create(parent=sset, dataset=self.dataset)

        with mock.patch('sa_api_v1.models.Place.cache.clear_instance') as mockclear:
            place.clear_instance_cache()

            # Now the cached info should be gone again
            self.assertEqual(mockclear.call_count, 0)


class MiscCacheClearingTests (TestCase):
    def test_new_submission_clears_v1_tabular_cache(self):
        """
        Related to a bug discovered in the Manager where the submission table
        downloads would not get new values on subsequent downloads. This test
        confirms that behavior.
        (2014 Feb 11)
        """
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        SubmissionSet.objects.all().delete()
        Submission.objects.all().delete()
        Action.objects.all().delete()
        cache.clear()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)
        self.place = Place.objects.create(dataset_id=self.dataset.id,
                                          geometry='POINT(0 0)')
        self.comment_set = SubmissionSet.objects.create(place_id=self.place.id,
                                                        name='comments')

        from sa_api_v1 import views as v1_views
        kwargs = {
            'submission_type': self.comment_set.name,
            'dataset__slug': self.dataset.slug,
            'dataset__owner__username': self.owner.username
        }
        request = RequestFactory().get(reverse('v1:tabular_all_submissions_by_dataset', kwargs=kwargs))
        view = v1_views.TabularAllSubmissionCollectionsView.as_view()

        # Create a couple submissions
        self.comments = [
            Submission.objects.create(parent_id=self.comment_set.id, dataset_id=self.dataset.id),
            Submission.objects.create(parent_id=self.comment_set.id, dataset_id=self.dataset.id)
        ]

        # Get table
        response1 = view(request, **kwargs)

        # Get table again, and ensure it's from cache, and it's the same
        response2 = view(request, **kwargs)
        self.assertEqual(response1.content, response2.content)

        # Create another subimssion
        Submission.objects.create(parent_id=self.comment_set.id, dataset_id=self.dataset.id)

        # Get table and ensure it's different
        response3 = view(request, **kwargs)
        self.assertNotEqual(response1.content, response3.content)


class PlacePermissionTests (TestCase):
    def clear_objects(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        SubmissionSet.objects.all().delete()
        Submission.objects.all().delete()
        Action.objects.all().delete()
        ApiKey.objects.all().delete()
        cache.clear()

    def test_group_permissions_can_restrict_reading(self):
        self.clear_objects()

        owner = User.objects.create(username='myowner')
        user = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
        place = Place.objects.create(dataset_id=dataset.id, geometry='POINT(0 0)')
        comment_set = SubmissionSet.objects.create(place_id=place.id, name='comments')

        # Create a key for the dataset
        key = ApiKey.objects.create(key='abc')
        key.datasets.add(dataset)

        # Make sure a permission objects were created
        self.assertEqual(dataset.permissions.count(), 1)
        self.assertEqual(key.permissions.count(), 1)

        # Get rid of the dataset permissions
        dataset.permissions.all().delete()

        # Revoke read permission on the key
        permission = key.permissions.all()[0]
        permission.can_retrieve = False
        permission.save()

        # Make sure we're not allowed to read.
        has_permission = check_data_permission(user, key, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, False)
