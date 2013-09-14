#-*- coding:utf-8 -*-

from django.test import TestCase
from nose.tools import istest
from sa_api_v2.models import Attachment
from sa_api_v2.serializers import AttachmentSerializer


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
