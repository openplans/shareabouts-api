#-*- coding:utf-8 -*-

from django.test import TestCase
from django.test.client import RequestFactory
from nose.tools import istest
from sa_api_v2.models import Attachment, Action, User, DataSet, Place, SubmissionSet, Submission
from sa_api_v2.serializers import AttachmentSerializer, ActionSerializer


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
