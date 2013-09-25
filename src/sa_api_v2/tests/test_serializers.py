#-*- coding:utf-8 -*-

from django.test import TestCase
from django.test.client import RequestFactory
from nose.tools import istest
from sa_api_v2.models import Attachment, Action, User, DataSet, Place, SubmissionSet, Submission
from sa_api_v2.serializers import AttachmentSerializer, ActionSerializer, UserSerializer
from social.apps.django_app.default.models import UserSocialAuth
import json
from os import path


class TestAttachmentSerializer (TestCase):

    def setUp(self):
        self.attachment_model = Attachment(name='my_file')

    def test_attributes(self):
        serializer = AttachmentSerializer(self.attachment_model)
        self.assertNotIn('id', serializer.data)
        self.assertNotIn('thing', serializer.data)

        self.assertIn('created_datetime', serializer.data)
        self.assertIn('updated_datetime', serializer.data)
        self.assertIn('file', serializer.data)
        self.assertIn('name', serializer.data)


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
        comments = SubmissionSet.objects.create(place=place, name='comments')
        comment = Submission.objects.create(dataset=dataset, parent=comments)
        
        self.place_action = Action.objects.create(thing=place.submittedthing_ptr)
        self.comment_action = Action.objects.create(thing=comment.submittedthing_ptr)

    def test_place_action_attributes(self):
        serializer = ActionSerializer(self.place_action)
        serializer.context = {
            'request': RequestFactory().get('')
        }

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'place')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)

    def test_submission_action_attributes(self):
        serializer = ActionSerializer(self.comment_action)
        serializer.context = {
            'request': RequestFactory().get('')
        }

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'comments')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)

    def test_prejoined_place_action_attributes(self):
        action = Action.objects.all()\
            .select_related('thing__place' ,'thing__submission')\
            .filter(thing=self.place_action.thing)[0]

        serializer = ActionSerializer(action)
        serializer.context = {
            'request': RequestFactory().get('')
        }

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'place')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)

    def test_prejoined_submission_action_attributes(self):
        action = Action.objects.all()\
            .select_related('thing__place' ,'thing__submission')\
            .filter(thing=self.comment_action.thing)[0]

        serializer = ActionSerializer(action)
        serializer.context = {
            'request': RequestFactory().get('')
        }

        self.assertIn('id', serializer.data)
        self.assertEqual(serializer.data.get('action'), 'create')
        self.assertEqual(serializer.data.get('target_type'), 'comments')
        self.assertIn('target', serializer.data)
        self.assertNotIn('thing', serializer.data)


class TestUserSerializer (TestCase):

    def setUp(self):
        test_dir = path.dirname(__file__)
        fixture_dir = path.join(test_dir, 'fixtures')
        twitter_user_data_file = path.join(fixture_dir, 'twitter_user.json')
        facebook_user_data_file = path.join(fixture_dir, 'facebook_user.json')

        self.twitter_user = User.objects.create_user(
            username='my_twitter_user', password='mypassword')
        self.twitter_social_auth = UserSocialAuth.objects.create(
            user=self.twitter_user, provider='twitter', uid='1234', 
            extra_data=json.load(open(twitter_user_data_file)))

        self.facebook_user = User.objects.create_user(
            username='my_facebook_user', password='mypassword')
        self.facebook_social_auth = UserSocialAuth.objects.create(
            user=self.facebook_user, provider='facebook', uid='1234', 
            extra_data=json.load(open(facebook_user_data_file)))

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
