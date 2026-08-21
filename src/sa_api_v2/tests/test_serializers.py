from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from rest_framework.reverse import reverse
from sa_api_v2.cache import cache_buffer
from sa_api_v2.models import Attachment, Action, User, DataSet, Place, Submission, Group, AnonymousValues
from sa_api_v2.serializers import AttachmentSerializer, ActionSerializer, UserSerializer, FullUserSerializer, PlaceSerializer, DataSetSerializer, SubmissionSerializer
from sa_api_v2.views import PlaceInstanceView
from social_django.models import UserSocialAuth
import json
from os import path


class TestAttachmentSerializer (TestCase):

    def setUp(self):
        f = ContentFile('this is a test')
        f.name = 'my_file.txt'
        self.attachment_model = Attachment(name='my_file', file=f)

    def test_attributes(self):
        serializer = AttachmentSerializer(self.attachment_model)
        self.assertNotIn('id', serializer.data)
        self.assertNotIn('thing', serializer.data)

        self.assertIn('created_datetime', serializer.data)
        self.assertIn('updated_datetime', serializer.data)
        self.assertIn('file', serializer.data)
        self.assertIn('name', serializer.data)

    def test_can_serlialize_a_null_instance(self):
        serializer = AttachmentSerializer(None)
        data = serializer.data
        self.assertIsInstance(data, dict)


class TestActionSerializer (TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Action.objects.all().delete()

        owner = User.objects.create(username='myuser')
        dataset = DataSet.objects.create(slug='data',
                                         owner_id=owner.id)
        place = Place.objects.create(dataset=dataset, geometry='POINT(2 3)')
        comment = Submission.objects.create(dataset=dataset, place=place, set_name='comments')

        self.place_action = Action.objects.create(thing=place.submittedthing_ptr)
        self.comment_action = Action.objects.create(thing=comment.submittedthing_ptr)

    def test_place_action_attributes(self):
        serializer = ActionSerializer(self.place_action, context={
            'request': RequestFactory().get('')
        })

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'place')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)

    def test_submission_action_attributes(self):
        serializer = ActionSerializer(self.comment_action, context={
            'request': RequestFactory().get('')
        })

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'comments')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)

    def test_prejoined_place_action_attributes(self):
        action = Action.objects.all()\
            .select_related('thing__full_place', 'thing__full_submission')\
            .filter(thing=self.place_action.thing)[0]

        serializer = ActionSerializer(action, context={
            'request': RequestFactory().get('')
        })

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'place')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)

    def test_prejoined_submission_action_attributes(self):
        action = Action.objects.all()\
            .select_related('thing__full_place', 'thing__full_submission')\
            .filter(thing=self.comment_action.thing)[0]

        serializer = ActionSerializer(action, context={
            'request': RequestFactory().get('')
        })

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'comments')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)


class TestSocialUserSerializer (TestCase):

    def setUp(self):
        test_dir = path.dirname(__file__)
        fixture_dir = path.join(test_dir, 'fixtures')
        twitter_user_data_file = path.join(fixture_dir, 'twitter_user.json')
        facebook_user_data_file = path.join(fixture_dir, 'facebook_user.json')

        with open(twitter_user_data_file) as f:
            self.twitter_user = User.objects.create_user(
                username='my_twitter_user', password='mypassword')
            self.twitter_social_auth = UserSocialAuth.objects.create(
                user=self.twitter_user, provider='twitter', uid='1234',
                extra_data=json.load(f))

        with open(facebook_user_data_file) as f:
            self.facebook_user = User.objects.create_user(
                username='my_facebook_user', password='mypassword')
            self.facebook_social_auth = UserSocialAuth.objects.create(
                user=self.facebook_user, provider='facebook', uid='1234',
                extra_data=json.load(f))

        self.no_social_user = User.objects.create_user(
            username='my_antisocial_user', password='password')

    def tearDown(self):
        User.objects.all().delete()
        UserSocialAuth.objects.all().delete()

    def test_twitter_user_attributes(self):
        serializer = UserSerializer(self.twitter_user)
        self.assertNotIn('password', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('avatar_url', serializer.data)

        self.assertEqual(serializer.data['name'], 'Mjumbe Poe')
        self.assertEqual(serializer.data['avatar_url'], 'http://a0.twimg.com/profile_images/1101892515/dreadlocked_browntwitterbird-248x270_bigger.png')

    def test_facebook_user_attributes(self):
        serializer = UserSerializer(self.facebook_user)
        self.assertNotIn('password', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('avatar_url', serializer.data)

        self.assertEqual(serializer.data['name'], 'Mjumbe Poe')
        self.assertEqual(serializer.data['avatar_url'], 'https://fbcdn-profile-a.akamaihd.net/hprofile-ak-ash4/c17.0.97.97/55_512302020614_7565_s.jpg')

    def test_no_social_user_attributes(self):
        serializer = UserSerializer(self.no_social_user)
        self.assertNotIn('password', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('avatar_url', serializer.data)

        self.assertEqual(serializer.data['name'], '')
        self.assertEqual(serializer.data['avatar_url'], '')


class TestUserSerializer (TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='my_owning_user', password='mypassword')
        self.normal_user = User.objects.create_user(
            username='my_normal_user', password='password')
        self.special_user = User.objects.create_user(
            username='my_special_user', password='password')

        self.datasets = [
            DataSet.objects.create(owner=self.owner, slug='ds1'),
            DataSet.objects.create(owner=self.owner, slug='ds2')
        ]
        self.groups = [
            Group.objects.create(dataset=self.datasets[0], name='special users')
        ]

        self.special_user._groups.add(self.groups[0])

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        DataSet.objects.all().delete()

    def test_partial_serializer_does_not_return_a_users_groups(self):
        serializer = UserSerializer(self.special_user)
        self.assertNotIn('groups', serializer.data)

    def test_full_serializer_returns_an_empty_list_of_groups_for_normal_users(self):
        serializer = FullUserSerializer(self.normal_user)
        self.assertIn('groups', serializer.data)
        self.assertEqual(serializer.data['groups'], [])

    def test_full_serializer_returns_a_users_groups(self):
        request = RequestFactory().get('')
        serializer = FullUserSerializer(self.special_user, context={'request': request})
        self.assertIn('groups', serializer.data)
        self.assertEqual(serializer.data['groups'], [
            {
                'dataset': reverse('dataset-detail', request=request, kwargs={'dataset_slug': 'ds1', 'owner_username': 'my_owning_user'}),
                'name': 'special users'
            }
        ])


class TestPlaceSerializer (TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        cache_buffer.reset()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)
        self.place = Place.objects.create(dataset=self.dataset, geometry='POINT(2 3)', data=json.dumps({'public-attr': 1, 'private-attr': 2}))
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')

    def test_can_serlialize_a_null_instance(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        serializer = PlaceSerializer(None, context={'request': request})

        data = serializer.data
        self.assertIsInstance(data, dict)

    def test_place_has_right_number_of_submissions(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        serializer = PlaceSerializer(self.place, context={'request': request})

        self.assertEqual(serializer.data['submission_sets']['comments']['length'], 2)

    def test_place_hides_private_data_by_default(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        serializer = PlaceSerializer(self.place, context={'request': request})

        self.assertIn('public-attr', serializer.data)
        self.assertNotIn('private-attr', serializer.data)

    def test_place_includes_private_data_when_specified(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        serializer = PlaceSerializer(self.place, context={'request': request, 'include_private': True})

        self.assertIn('public-attr', serializer.data)
        self.assertIn('private-attr', serializer.data)

    def test_place_partial_update(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        view = PlaceInstanceView()
        view.request = request

        serializer = PlaceSerializer(
            self.place,
            context={'view': view, 'request': request, 'include_private': True},
            data={'private-attr': 4, 'new-attr': 5, 'geometry': 'POINT(4 5)'},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(json.loads(self.place.data), {'public-attr': 1, 'private-attr': 4, 'new-attr': 5})
        self.assertEqual(self.place.geometry.wkt, GEOSGeometry('POINT(4 5)').wkt)

    def test_visible_has_truthy_boolean_values(self):
        # You should be able to use case-insensitive "on", "yes" and "true" for
        # the visible value (primarily for backwards compatibility).
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        view = PlaceInstanceView()
        view.request = request

        self.place.visible = False
        self.place.save()
        self.place.refresh_from_db()

        self.assertTrue(not self.place.visible)

        serializer = PlaceSerializer(
            self.place,
            context={'view': view, 'request': request},
            data={'visible': 'On'},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.place.refresh_from_db()

        self.assertTrue(self.place.visible)


class TestSubmissionSerializer (TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        cache_buffer.reset()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)
        self.place = Place.objects.create(dataset=self.dataset, geometry='POINT(2 3)')
        self.submission = Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments', data=json.dumps({'public-attr': 1, 'private-attr': 2}))

    def test_can_serlialize_a_null_instance(self):
        serializer = SubmissionSerializer(None, context={
            'request': RequestFactory().get('')
        })

        data = serializer.data
        self.assertIsInstance(data, dict)

    def test_submission_hides_private_data_by_default(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        serializer = SubmissionSerializer(self.submission, context={'request': request})

        self.assertIn('public-attr', serializer.data)
        self.assertNotIn('private-attr', serializer.data)

    def test_submission_includes_private_data_when_specified(self):
        request = RequestFactory().get('')
        request.get_dataset = lambda: self.dataset

        serializer = SubmissionSerializer(self.submission, context={'request': request, 'include_private': True})

        self.assertIn('public-attr', serializer.data)
        self.assertIn('private-attr', serializer.data)


class TestDataSetSerializer (TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        cache_buffer.reset()

        self.owner = User.objects.create(username='myuser')
        self.dataset = DataSet.objects.create(slug='data',
                                              owner_id=self.owner.id)
        self.place = Place.objects.create(dataset=self.dataset, geometry='POINT(2 3)')
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')
        Submission.objects.create(dataset=self.dataset, place=self.place, set_name='comments')

    def test_can_serlialize_a_null_instance(self):
        serializer = DataSetSerializer(None, context={
            'request': RequestFactory().get(''),
            'place_count_map_getter': (lambda: {}),
            'submission_sets_map_getter': (lambda: {})
        })

        data = serializer.data
        self.assertIsInstance(data, dict)


class TestGroupAndMetadataSerializers (TestCase):

    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Group.objects.all().delete()

        self.owner = User.objects.create(username='groupowner')
        self.dataset = DataSet.objects.create(slug='groupds', owner=self.owner)
        self.group = Group.objects.create(
            dataset=self.dataset,
            name='reviewers',
            display_name='Code Reviewers',
            purpose='Review submissions'
        )

        from sa_api_v2.apikey.models import ApiKey
        from sa_api_v2.cors.models import Origin
        self.key = ApiKey.objects.create(
            dataset=self.dataset,
            key='testkey1',
            display_name='Key Name',
            purpose='Key Purpose'
        )
        self.origin = Origin.objects.create(
            dataset=self.dataset,
            pattern='http://localhost:8000',
            display_name='Origin Name',
            purpose='Origin Purpose'
        )

    def test_group_serializer_excludes_display_name_and_purpose(self):
        from sa_api_v2.serializers import GroupSerializer
        request = RequestFactory().get('')
        serializer = GroupSerializer(self.group, context={'request': request})
        self.assertIn('name', serializer.data)
        self.assertNotIn('display_name', serializer.data)
        self.assertNotIn('purpose', serializer.data)
        self.assertNotIn('submitters', serializer.data)

    def test_simple_group_serializer_includes_display_name_and_purpose(self):
        from sa_api_v2.serializers import SimpleGroupSerializer
        serializer = SimpleGroupSerializer(self.group)
        self.assertIn('name', serializer.data)
        self.assertIn('display_name', serializer.data)
        self.assertIn('purpose', serializer.data)
        self.assertEqual(serializer.data['display_name'], 'Code Reviewers')
        self.assertEqual(serializer.data['purpose'], 'Review submissions')
        self.assertNotIn('submitters', serializer.data)

    def test_api_key_serializer_includes_display_name_and_purpose(self):
        from sa_api_v2.serializers import ApiKeySerializer
        serializer = ApiKeySerializer(self.key)
        self.assertIn('key', serializer.data)
        self.assertIn('display_name', serializer.data)
        self.assertIn('purpose', serializer.data)
        self.assertEqual(serializer.data['display_name'], 'Key Name')
        self.assertEqual(serializer.data['purpose'], 'Key Purpose')

    def test_origin_serializer_includes_display_name_and_purpose(self):
        from sa_api_v2.serializers import OriginSerializer
        serializer = OriginSerializer(self.origin)
        self.assertIn('pattern', serializer.data)
        self.assertIn('display_name', serializer.data)
        self.assertIn('purpose', serializer.data)
        self.assertEqual(serializer.data['display_name'], 'Origin Name')
        self.assertEqual(serializer.data['purpose'], 'Origin Purpose')


class TestAnonymousDataSerialization (TestCase):
    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        Place.objects.all().delete()
        Submission.objects.all().delete()
        AnonymousValues.objects.all().delete()

        self.owner = User.objects.create(username='testowner')
        self.dataset = DataSet.objects.create(slug='testds', owner=self.owner)
        self.place = Place.objects.create(dataset=self.dataset, geometry='POINT(0 0)')

    def get_context(self, request):
        from rest_framework.views import APIView
        view = APIView()
        view.request = request
        request.get_dataset = lambda: self.dataset
        return {'view': view, 'request': request}

    def test_place_creation_with_anonymous_data(self):
        request = RequestFactory().post('', data={}, content_type='application/json')
        request.user = self.owner
        serializer = PlaceSerializer(data={
            'geometry': 'POINT(1 1)',
            'location_type': 'suggestion',
            'private_email': 'jane@example.com',
            'anonymous_age': '25-34',
            'anonymous_race': 'Asian'
        }, context=self.get_context(request))

        self.assertTrue(serializer.is_valid(), serializer.errors)
        place = serializer.save(dataset=self.dataset)

        # Place data blob excludes anonymous fields
        data_blob = json.loads(place.data)
        self.assertIn('location_type', data_blob)
        self.assertIn('private_email', data_blob)
        self.assertNotIn('anonymous_age', data_blob)
        self.assertNotIn('anonymous_race', data_blob)
        self.assertNotIn('age', data_blob)
        self.assertNotIn('race', data_blob)

        # Serializer representation excludes anonymous fields
        self.assertNotIn('anonymous_age', serializer.data)
        self.assertNotIn('anonymous_race', serializer.data)
        self.assertNotIn('age', serializer.data)
        self.assertNotIn('race', serializer.data)

        # AnonymousValues record created
        anon_records = AnonymousValues.objects.filter(dataset=self.dataset, set_name='places')
        self.assertEqual(anon_records.count(), 1)
        anon = anon_records.first()
        self.assertEqual(anon.data, {'age': '25-34', 'race': 'Asian'})

    def test_submission_creation_with_anonymous_data(self):
        request = RequestFactory().post('', data={}, content_type='application/json')
        request.user = self.owner
        serializer = SubmissionSerializer(data={
            'text': 'Great idea',
            'anonymous_age': '18-24'
        }, context=self.get_context(request))

        self.assertTrue(serializer.is_valid(), serializer.errors)
        submission = serializer.save(dataset=self.dataset, place=self.place, set_name='comments')

        data_blob = json.loads(submission.data)
        self.assertIn('text', data_blob)
        self.assertNotIn('anonymous_age', data_blob)
        self.assertNotIn('age', data_blob)

        anon_records = AnonymousValues.objects.filter(dataset=self.dataset, set_name='comments')
        self.assertEqual(anon_records.count(), 1)
        anon = anon_records.first()
        self.assertEqual(anon.data, {'age': '18-24'})

    def test_submission_creation_with_complex_anonymous_values(self):
        request = RequestFactory().post('', data={}, content_type='application/json')
        request.user = self.owner
        serializer = SubmissionSerializer(data={
            'idhash': 'abc123',
            'has_voted': True,
            'anonymous_proposals': ['proposal-A', 'proposal-B', 'proposal-C']
        }, context=self.get_context(request))

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save(dataset=self.dataset, place=self.place, set_name='ballots')

        anon_records = AnonymousValues.objects.filter(dataset=self.dataset, set_name='ballots')
        self.assertEqual(anon_records.count(), 1)
        anon = anon_records.first()
        self.assertEqual(anon.data, {'proposals': ['proposal-A', 'proposal-B', 'proposal-C']})

    def test_no_anonymous_row_when_all_values_null_or_empty(self):
        request = RequestFactory().post('', data={}, content_type='application/json')
        request.user = self.owner
        serializer = PlaceSerializer(data={
            'geometry': 'POINT(1 1)',
            'location_type': 'park',
            'anonymous_age': None,
            'anonymous_race': ''
        }, context=self.get_context(request))

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save(dataset=self.dataset)

        self.assertEqual(AnonymousValues.objects.count(), 0)

    def test_mixed_null_and_non_null_anonymous_values(self):
        request = RequestFactory().post('', data={}, content_type='application/json')
        request.user = self.owner
        serializer = PlaceSerializer(data={
            'geometry': 'POINT(1 1)',
            'location_type': 'park',
            'anonymous_age': '25-34',
            'anonymous_race': None
        }, context=self.get_context(request))

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save(dataset=self.dataset)

        anon_records = AnonymousValues.objects.filter(dataset=self.dataset, set_name='places')
        self.assertEqual(anon_records.count(), 1)
        self.assertEqual(anon_records.first().data, {'age': '25-34', 'race': None})

    def test_no_anonymous_values_created_when_no_anonymous_fields(self):
        request = RequestFactory().post('', data={}, content_type='application/json')
        request.user = self.owner
        serializer = PlaceSerializer(data={
            'geometry': 'POINT(1 1)',
            'location_type': 'suggestion'
        }, context=self.get_context(request))

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save(dataset=self.dataset)

        self.assertEqual(AnonymousValues.objects.count(), 0)


