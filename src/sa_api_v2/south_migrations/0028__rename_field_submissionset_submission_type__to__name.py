# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'SubmissionSet', fields ['submission_type', 'place']
        db.delete_unique(u'sa_api_submissionset', ['submission_type', 'place_id'])

        # Renaming field 'SubmissionSet.submission_type' to 'SubmissionSet.name'
        db.rename_column(u'sa_api_submissionset', 'submission_type', 'name')

        # Adding unique constraint on 'SubmissionSet', fields ['place', 'name']
        db.create_unique(u'sa_api_submissionset', ['place_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'SubmissionSet', fields ['place', 'name']
        db.delete_unique(u'sa_api_submissionset', ['place_id', 'name'])

        # Renaming field 'SubmissionSet.name' to 'SubmissionSet.submission_type'
        db.rename_column(u'sa_api_submissionset', 'name', 'submission_type')

        # Adding unique constraint on 'SubmissionSet', fields ['submission_type', 'place']
        db.create_unique(u'sa_api_submissionset', ['submission_type', 'place_id'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sa_api_v2.activity': {
            'Meta': {'object_name': 'Activity', 'db_table': "'sa_api_activity'"},
            'action': ('django.db.models.fields.CharField', [], {'default': "'create'", 'max_length': '16'}),
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sa_api_v2.SubmittedThing']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sa_api_v2.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': u"orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sa_api_v2.dataset': {
            'Meta': {'unique_together': "(('owner', 'slug'),)", 'object_name': 'DataSet'},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "u''", 'max_length': '128'})
        },
        u'sa_api_v2.place': {
            'Meta': {'object_name': 'Place', '_ormbases': [u'sa_api_v2.SubmittedThing']},
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            u'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'sa_api_v2.submission': {
            'Meta': {'object_name': 'Submission', '_ormbases': [u'sa_api_v2.SubmittedThing']},
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'to': u"orm['sa_api_v2.SubmissionSet']"}),
            u'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'sa_api_v2.submissionset': {
            'Meta': {'unique_together': "(('place', 'name'),)", 'object_name': 'SubmissionSet'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submission_sets'", 'to': u"orm['sa_api_v2.Place']"})
        },
        u'sa_api_v2.submittedthing': {
            'Meta': {'object_name': 'SubmittedThing', 'db_table': "'sa_api_submittedthing'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted_thing_set'", 'blank': 'True', 'to': u"orm['sa_api_v2.DataSet']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submitter_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['sa_api_v2']
