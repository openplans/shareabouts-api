import json
from django.test import TestCase
# from django.test.client import Client
from django.test.client import RequestFactory
# from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
# from mock import patch
# from nose.tools import (istest, assert_equal, assert_not_equal, assert_in,
#                         assert_raises)
from ..models import (Attachment, DataSet, User, Group, SubmittedThing, Action, Place, Submission,
    DataSetPermission, check_data_permission, DataIndex, IndexedValue)
from ..apikey.models import ApiKey
# from ..views import SubmissionCollectionView
# from ..views import raise_error_if_not_authenticated
# from ..views import ApiKeyCollectionView
# from ..views import OwnerPasswordView
# import json
import mock
from mock import patch


import os.path
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')

class TestAttachment (TestCase):
    def setUp(self):
        self.owner = User.objects.create(username='user')
        self.dataset = DataSet.objects.create(slug='data', owner=self.owner)
        self.place = Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')

        from django.core.files.images import ImageFile
        image_path = os.path.join(FIXTURE_PATH, 'Automated-Testing.jpg')
        self.image_file = ImageFile(open(image_path, mode='rb'), name='Automated-Testing.jpg')

        from django.core.files.base import ContentFile
        self.non_image_file = ContentFile('This is not an image.')

    def tearDown(self):
        User.objects.all().delete()  # Cascades.
        self.image_file.close()

    def test_save_sets_image_dims_when_none_is_provided(self):
        a = Attachment(thing=self.place, file=self.image_file)

        self.assertIsNone(a.width)
        self.assertIsNone(a.height)
        a.save()
        self.assertIsNotNone(a.width)
        self.assertIsNotNone(a.height)

    def test_save_leaves_image_dims_when_already_set(self):
        IMAGE_DIM = 23049
        a = Attachment(thing=self.place, file=self.image_file, width=IMAGE_DIM, height=IMAGE_DIM)

        a.save()
        self.assertEqual(a.width, IMAGE_DIM)
        self.assertEqual(a.height, IMAGE_DIM)

    def test_save_ignores_image_dims_when_not_an_image_file(self):
        a = Attachment(thing=self.place, file=self.non_image_file)

        a.save()
        self.assertIsNone(a.width)
        self.assertIsNone(a.height)


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
        self.dataset.indexes.add(DataIndex(attr_name='index1'), bulk=False)
        self.dataset.indexes.add(DataIndex(attr_name='index2'), bulk=False)

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

        self.dataset.indexes.add(DataIndex(attr_name='index1'), bulk=False)
        self.dataset.indexes.add(DataIndex(attr_name='index2'), bulk=False)

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

        self.dataset.indexes.add(DataIndex(attr_name='index1'), bulk=False)
        self.dataset.indexes.add(DataIndex(attr_name='index2'), bulk=False)

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
        self.dataset.indexes.add(DataIndex(attr_name='index'), bulk=False)

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

        self.dataset.indexes.add(DataIndex(attr_name='index'), bulk=False)
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
        clone_data = json.loads(clone.data)
        clone_data['new-field'] = 'new-value'
        clone.data = json.dumps(clone_data)
        clone.save()
        self.assertNotEqual(clone.set_name, submission.set_name)
        self.assertNotEqual(clone.data, submission.data)

        # Reload the objects from the database and check that the comparisons
        # still hold.
        submission = Submission.objects.get(pk=submission.id)
        clone = Submission.objects.get(pk=clone.id)
        self.assertNotEqual(json.loads(clone.data), json.loads(submission.data))
        self.assertNotEqual(clone.set_name, submission.set_name)
        self.assertNotEqual(clone.data, submission.data)

    def test_place_can_be_cloned(self):
        dataset = DataSet.objects.create(owner=self.owner, slug='dataset')
        place = Place.objects.create(dataset=dataset, geometry='POINT(0 0)')
        Submission.objects.create(dataset=dataset, place=place, set_name='comments', data='{"field": "value1"}')
        Submission.objects.create(dataset=dataset, place=place, set_name='comments', data='{"field": "value2"}')
        Submission.objects.create(dataset=dataset, place=place, set_name='support')

        # Clone the object and make sure the clone's values are initialized
        # correctly.
        clone = place.clone()
        self.assertEqual(clone.dataset, place.dataset)
        self.assertEqual(clone.geometry, place.geometry)
        self.assertEqual(clone.submissions.count(), place.submissions.count())
        self.assertNotEqual(clone.id, place.id)

        # Make sure the clone and the original have no actual submissions in
        # common.
        clone_submissions = clone.submissions.all()
        place_submissions = place.submissions.all()

        clone_submission_set_names = sorted([s.set_name for s in clone_submissions])
        place_submission_set_names = sorted([s.set_name for s in place_submissions])
        self.assertEqual(clone_submission_set_names, place_submission_set_names)

        clone_submission_ids = set([s.id for s in clone_submissions])
        place_submission_ids = set([s.id for s in place_submissions])
        self.assertEqual(clone_submission_ids & place_submission_ids, set())

        # Change a property on the clone and make sure that they're different
        # (i.e., not aliases of the same thing).
        clone.geometry = 'POINT(1 1)'
        clone.save()
        self.assertNotEqual(clone.geometry, place.geometry)

        # Reload the objects from the database and check that the comparisons
        # still hold.
        place = Place.objects.get(pk=place.id)
        clone = Place.objects.get(pk=clone.id)
        self.assertNotEqual(clone.geometry, place.geometry)

    def test_dataset_can_be_cloned(self):
        dataset = DataSet.objects.create(owner=self.owner, slug='dataset')
        place1 = Place.objects.create(dataset=dataset, geometry='POINT(0 0)')
        Submission.objects.create(dataset=dataset, place=place1, set_name='comments', data='{"field": "value1"}')
        Submission.objects.create(dataset=dataset, place=place1, set_name='comments', data='{"field": "value2"}')
        Submission.objects.create(dataset=dataset, place=place1, set_name='support')
        place2 = Place.objects.create(dataset=dataset, geometry='POINT(1 1)')
        Submission.objects.create(dataset=dataset, place=place2, set_name='comments')
        Submission.objects.create(dataset=dataset, place=place2, set_name='support')

        apikey = dataset.keys.create(key='somekey')
        apikey.permissions.all().delete()
        apikey.permissions.create(submission_set='comments', can_retrieve=True, can_create=True)

        origin = dataset.origins.create(pattern='someorigin.com')
        origin.permissions.all().delete()
        origin.permissions.create(submission_set='comments', can_retrieve=True, can_create=True)

        # Clone the object and make sure the clone's values are initialized
        # correctly.
        clone = dataset.clone(overrides={'slug': 'dataset-2'})
        self.assertEqual(clone.owner, dataset.owner)
        self.assertEqual(clone.things.count(), dataset.things.count())
        self.assertNotEqual(clone.id, dataset.id)

        # Make sure the clone and the original have no actual submissions in
        # common.
        clone_submissions = clone.things.filter(full_submission__isnull=False)
        orgnl_submissions = dataset.things.filter(full_submission__isnull=False)

        clone_submission_set_names = sorted([s.full_submission.set_name for s in clone_submissions])
        orgnl_submission_set_names = sorted([s.full_submission.set_name for s in orgnl_submissions])
        self.assertEqual(clone_submission_set_names, orgnl_submission_set_names)

        clone_submission_ids = set([s.id for s in clone_submissions])
        orgnl_submission_ids = set([s.id for s in orgnl_submissions])
        self.assertEqual(clone_submission_ids & orgnl_submission_ids, set())

        clone_places = clone.things.filter(full_place__isnull=False)
        orgnl_places = dataset.things.filter(full_place__isnull=False)

        clone_place_ids = set([s.id for s in clone_places])
        orgnl_place_ids = set([s.id for s in orgnl_places])
        self.assertEqual(clone_place_ids & orgnl_place_ids, set())

        # Make sure the clone and the original have the same values (but not
        # references) for keys and origins.
        self.assertEqual(dataset.permissions.count(), clone.permissions.count())
        self.assertEqual(dataset.keys.count(), clone.keys.count())
        self.assertEqual(dataset.origins.count(), clone.origins.count())

        clone_key_ids = set([k.id for k in clone.keys.all()])
        orgnl_key_ids = set([k.id for k in dataset.keys.all()])
        self.assertEqual(clone_key_ids & orgnl_key_ids, set())

        clone_orgn_ids = set([o.id for o in clone.origins.all()])
        orgnl_orgn_ids = set([o.id for o in dataset.origins.all()])
        self.assertEqual(clone_orgn_ids & orgnl_orgn_ids, set())

        clonekey = dataset.keys.get(key=apikey.key)
        self.assertEqual(apikey.permissions.count(), clonekey.permissions.count())

        cloneorigin = dataset.origins.get(pattern=origin.pattern)
        self.assertEqual(origin.permissions.count(), cloneorigin.permissions.count())

    def test_group_can_be_cloned(self):
        dataset = DataSet.objects.create(owner=self.owner, slug='dataset')
        user1 = User.objects.create(username='user1')
        user2 = User.objects.create(username='user2')
        group = Group.objects.create(dataset=dataset, name='users')
        group.submitters.add(user1)
        group.submitters.add(user2)

        # Clone the object and make sure the clone's values are initialized
        # correctly.
        clone = group.clone(overrides={'name': 'users-2'})
        self.assertEqual(clone.dataset, group.dataset)
        self.assertNotEqual(clone.id, group.id)

        clone_submitters = clone.submitters.all()
        group_submitters = group.submitters.all()

        clone_submitter_ids = set([s.id for s in clone_submitters])
        group_submitter_ids = set([s.id for s in group_submitters])
        self.assertEqual(clone_submitter_ids, group_submitter_ids)

    def test_apikey_can_be_cloned(self):
        dataset = DataSet.objects.create(owner=self.owner, slug='dataset')
        key = ApiKey.objects.create(dataset=dataset)

        # Clone the object and make sure the clone's values are initialized
        # correctly.
        clone = key.clone()
        self.assertEqual(clone.dataset, key.dataset)
        self.assertNotEqual(clone.id, key.id)

        # Keys must not repeat across system
        self.assertNotEqual(clone.key, key.key)


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
        dataset.permissions.add(places_perm, bulk=False)

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
