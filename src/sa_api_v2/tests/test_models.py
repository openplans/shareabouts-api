import json
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
from ..models import (DataSet, User, SubmittedThing, Action, Place, Submission,
    DataSetPermission, check_data_permission, DataIndex, IndexedValue)
from ..apikey.models import ApiKey
# from ..views import SubmissionCollectionView
# from ..views import raise_error_if_not_authenticated
# from ..views import ApiKeyCollectionView
# from ..views import OwnerPasswordView
# import json
import mock
from mock import patch


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


class TestDataIndexes (TestCase):
    def setUp(self):
        User.objects.all().delete()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)

    def tearDown(self):
        User.objects.all().delete()  # Everything should cascade from owner

    def test_indexed_values_are_indexed_when_thing_is_saved(self):
        self.dataset.indexes.add(DataIndex(attr_name='index1'))
        self.dataset.indexes.add(DataIndex(attr_name='index2'))

        st1 = SubmittedThing(dataset=self.dataset)
        st1.data = '{"index1": "value1", "index2": 2, "freetext": "This is an unindexed value."}'
        st1.save()

        indexed_values = IndexedValue.objects.filter(index__dataset=self.dataset)
        self.assertEqual(indexed_values.count(), 2)
        self.assertEqual(set([value.value for value in indexed_values]), set(['value1', '2']))

    def test_indexed_values_are_indexed_when_index_is_saved(self):
        st1 = SubmittedThing(dataset=self.dataset)
        st1.data = '{"index1": "value1", "index2": 2, "freetext": "This is an unindexed value."}'
        st1.save()

        self.dataset.indexes.add(DataIndex(attr_name='index1'))
        self.dataset.indexes.add(DataIndex(attr_name='index2'))

        indexed_values = IndexedValue.objects.filter(index__dataset=self.dataset)
        self.assertEqual(indexed_values.count(), 2)
        self.assertEqual(set([value.value for value in indexed_values]), set(['value1', '2']))

    def test_user_can_query_by_indexed_value(self):
        st1 = SubmittedThing(dataset=self.dataset)
        st1.data = '{"index1": "value1", "index2": 2, "somefreetext": "This is an unindexed value."}'
        st1.save()

        st2 = SubmittedThing(dataset=self.dataset)
        st2.data = '{"index1": "value_not1", "index2": "2", "morefreetext": "This is an unindexed value."}'
        st2.save()

        st3 = SubmittedThing(dataset=DataSet.objects.create(slug='temp-dataset', owner=self.owner))
        st3.data = '{"index1": "value1", "index2": 2}'
        st3.save()

        self.dataset.indexes.add(DataIndex(attr_name='index1'))
        self.dataset.indexes.add(DataIndex(attr_name='index2'))

        # index1 only has one value matching 'value1' in self.dataset
        qs = self.dataset.things.filter_by_index('index1', 'value1')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(json.loads(qs[0].data)['index1'], 'value1')

        # index2 has two values matching 2 in self.dataset, even though one's
        # a string and one's a number
        qs = self.dataset.things.filter_by_index('index2', '2')
        self.assertEqual(qs.count(), 2)

    def test_get_returns_the_true_value_of_an_indexed_value(self):
        st1 = SubmittedThing(dataset=self.dataset)
        st1.data = '{"index1": "value1", "index2": 2, "freetext": "This is an unindexed value."}'
        st1.save(reindex=False)

        index1 = DataIndex(attr_name='index1', dataset=self.dataset)
        index1.save(reindex=False)

        index2 = DataIndex(attr_name='index2', dataset=self.dataset)
        index2.save(reindex=False)

        IndexedValue.objects.create(value='value1', thing=st1, index=index1)
        IndexedValue.objects.create(value=2, thing=st1, index=index2)

        indexed_values = IndexedValue.objects.filter(index__dataset=self.dataset)
        self.assertEqual(indexed_values.count(), 2)
        self.assertEqual(set([value.get() for value in indexed_values]), set(['value1', 2]))

    def test_indexed_value_get_raises_KeyError_if_value_is_not_found(self):
        st = SubmittedThing(dataset=self.dataset)
        st.data = '{"index1": "value1", "freetext": "This is an unindexed value."}'
        st.save(reindex=False)

        index = DataIndex(attr_name='index2', dataset=self.dataset)
        index.save(reindex=False)

        indexed_value = IndexedValue.objects.create(value=2, thing=st, index=index)

        with self.assertRaises(KeyError):
            indexed_value.get()

    def test_data_values_are_updated_when_saved(self):
        self.dataset.indexes.add(DataIndex(attr_name='index'))

        st1 = SubmittedThing(dataset=self.dataset)
        st1.data = '{"index": "value1", "freetext": "This is an unindexed value."}'
        st1.save()
        st1.data = '{"index": "value2", "freetext": "This is an unindexed value."}'
        st1.save()

        indexed_values = IndexedValue.objects.filter(index__dataset=self.dataset)
        self.assertEqual(indexed_values.count(), 1)
        self.assertEqual(set([value.value for value in indexed_values]), set(['value2']))

    def test_data_values_are_deleted_when_removed(self):
        st1 = SubmittedThing(dataset=self.dataset)
        st1.data = '{"index": "value1", "somefreetext": "This is an unindexed value."}'
        st1.save()

        st2 = SubmittedThing(dataset=self.dataset)
        st2.data = '{"index": "value_not1", "morefreetext": "This is an unindexed value."}'
        st2.save()

        st3 = SubmittedThing(dataset=self.dataset)
        st3.data = '{"index": "value1"}'
        st3.save()

        self.dataset.indexes.add(DataIndex(attr_name='index'))
        num_indexed_values = IndexedValue.objects.all().count()

        # At first, index with 'value1' should match two things.
        qs = self.dataset.things.filter_by_index('index', 'value1')
        self.assertEqual(qs.count(), 2)

        st1.delete()

        # Now, index with 'value1' should only match one things.
        qs = self.dataset.things.filter_by_index('index', 'value1')
        self.assertEqual(qs.count(), 1)

        # Delete should have cascaded to indexed values.
        self.assertEqual(IndexedValue.objects.all().count(), num_indexed_values - 1)


class CloningTests (TestCase):
    def clear_objects(self):
        # This should cascade to everything else.
        User.objects.all().delete()

    def tearDown(self):
        self.clear_objects()

    def setUp(self):
        self.clear_objects()
        self.owner = User.objects.create(username='myuser')

    def test_submission_can_be_cloned(self):
        dataset = DataSet.objects.create(owner=self.owner, slug='dataset')
        place = Place.objects.create(dataset=dataset, geometry='POINT(0 0)')
        submission = Submission.objects.create(dataset=dataset, place=place, set_name='comments', data='{"field": "value"}')

        # Clone the object and make sure the clone's values are initialized
        # correctly.
        clone = submission.clone()
        self.assertEqual(clone.dataset, submission.dataset)
        self.assertEqual(clone.place, submission.place)
        self.assertEqual(clone.set_name, submission.set_name)
        self.assertEqual(json.loads(clone.data), json.loads(submission.data))
        self.assertNotEqual(clone.id, submission.id)

        # Change a property on the clone and make sure that they're different
        # (i.e., not aliases of the same thing).
        clone.set_name = 'support'
        clone.save()
        self.assertNotEqual(clone.set_name, submission.set_name)

        # Reload the objects from the database and check that the comparisons
        # still hold.
        submission = Submission.objects.get(pk=submission.id)
        clone = Submission.objects.get(pk=clone.id)
        self.assertEqual(json.loads(clone.data), json.loads(submission.data))
        self.assertNotEqual(clone.set_name, submission.set_name)


class DataPermissionTests (TestCase):
    def clear_objects(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        Action.objects.all().delete()
        ApiKey.objects.all().delete()
        cache.clear()

    def setUp(self):
        self.clear_objects()

    def tearDown(self):
        self.clear_objects()

    def test_default_dataset_permissions_allow_reading(self):
        owner = User.objects.create(username='myowner')
        user = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
        place = Place.objects.create(dataset_id=dataset.id, geometry='POINT(0 0)')

        # Make sure a permission objects were created
        self.assertEqual(dataset.permissions.count(), 1)

        # Make sure anonymous is allowed to read, not write.
        self.assertEqual(check_data_permission(None, None, 'retrieve', dataset, 'comments'), True)
        self.assertEqual(check_data_permission(None, None, 'update', dataset, 'comments'), False)
        self.assertEqual(check_data_permission(None, None, 'create', dataset, 'comments'), False)
        self.assertEqual(check_data_permission(None, None, 'destroy', dataset, 'comments'), False)

        # Make sure authenticated is allowed to read.
        self.assertEqual(check_data_permission(user, None, 'retrieve', dataset, 'comments'), True)
        self.assertEqual(check_data_permission(user, None, 'update', dataset, 'comments'), False)
        self.assertEqual(check_data_permission(user, None, 'create', dataset, 'comments'), False)
        self.assertEqual(check_data_permission(user, None, 'destroy', dataset, 'comments'), False)

        # Make sure owner is allowed to read.
        self.assertEqual(check_data_permission(owner, None, 'retrieve', dataset, 'comments'), True)
        self.assertEqual(check_data_permission(owner, None, 'update', dataset, 'comments'), True)
        self.assertEqual(check_data_permission(owner, None, 'create', dataset, 'comments'), True)
        self.assertEqual(check_data_permission(owner, None, 'destroy', dataset, 'comments'), True)

    def test_dataset_permissions_can_restrict_reading(self):
        owner = User.objects.create(username='myowner')
        user = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
        place = Place.objects.create(dataset_id=dataset.id, geometry='POINT(0 0)')

        # Make sure a permission objects were created
        self.assertEqual(dataset.permissions.count(), 1)

        # Turn off read access
        perm = dataset.permissions.all().get()
        perm.can_retrieve = False
        perm.save()

        # Make sure anonymous is not allowed to read.
        has_permission = check_data_permission(None, None, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, False)

        # Make sure authenticated is not allowed to read.
        has_permission = check_data_permission(user, None, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, False)

        # Make sure owner is allowed to read.
        has_permission = check_data_permission(owner, None, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, True)

    def test_specific_dataset_permissions_can_allow_or_restrict_reading(self):
        owner = User.objects.create(username='myowner')
        user = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
        place = Place.objects.create(dataset_id=dataset.id, geometry='POINT(0 0)')

        # Make sure a permission objects were created
        self.assertEqual(dataset.permissions.count(), 1)

        # Turn on read access for comments, but off for places
        comments_perm = dataset.permissions.all().get()
        comments_perm.submission_set = 'comments'
        comments_perm.save()

        places_perm = DataSetPermission(submission_set='places')
        places_perm.can_retrieve = False
        dataset.permissions.add(places_perm)

        # Make sure anonymous can read comments, but not places.
        has_permission = check_data_permission(None, None, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, True)

        has_permission = check_data_permission(None, None, 'retrieve', dataset, 'places')
        self.assertEqual(has_permission, False)

        # Make sure authenticated can read comments, but not places.
        has_permission = check_data_permission(user, None, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, True)

        has_permission = check_data_permission(user, None, 'retrieve', dataset, 'places')
        self.assertEqual(has_permission, False)

        # Make sure owner is allowed to read everything.
        has_permission = check_data_permission(owner, None, 'retrieve', dataset, 'comments')
        self.assertEqual(has_permission, True)

        has_permission = check_data_permission(owner, None, 'retrieve', dataset, 'places')
        self.assertEqual(has_permission, True)

    def test_group_permissions_can_restrict_reading(self):
        owner = User.objects.create(username='myowner')
        user = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
        place = Place.objects.create(dataset_id=dataset.id, geometry='POINT(0 0)')

        # Create a key for the dataset
        key = ApiKey.objects.create(key='abc', dataset=dataset)

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

    def test_fails_when_requesting_an_unknown_permission(self):
        user = client = dataset = submission_set = None
        with self.assertRaises(ValueError):
            check_data_permission(user, client, 'obliterate', dataset, submission_set)

    def test_accepts_submission_set_name(self):
        owner = User.objects.create(username='myowner')
        user = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data', owner_id=owner.id)
        place = Place.objects.create(dataset_id=dataset.id, geometry='POINT(0 0)')

        with patch('sa_api_v2.models.data_permissions.any_allow') as any_allow:
            check_data_permission(user, None, 'retrieve', dataset, 'comments')
            self.assertEqual(any_allow.call_args[0][2], 'comments')


# More permissions tests to write:
# - General client permission allows reading and restricts writing
# - Specific client permission allows/restricts reading and writing
# - General group permission allows reading and restricts writing
# - Specific group permission allows/restricts reading and writing
