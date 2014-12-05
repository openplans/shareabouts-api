# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."

        Activity = orm['sa_api_v2.Activity']
        Place = orm['sa_api_v2.Place']
        Submission = orm['sa_api_v2.Submission']

        for activity in Activity.objects.all():
            if activity.data_object_id is None:
                activity.delete()
                continue

            try:
                if (activity.data_content_type.model.lower() == 'place'):
                    old_data = Place.objects.get(id=activity.data_object_id)
                elif (activity.data_content_type.model.lower() == 'submission'):
                    old_data = Submission.objects.get(id=activity.data_object_id)

                activity.data = old_data.submittedthing_ptr
            except (ValueError, NameError):
                activity.delete()
                continue

            activity.save()

    def backwards(self, orm):
        "Write your backwards methods here."

        Activity = orm['sa_api_v2.Activity']
        gfk = generic.GenericForeignKey('data_content_type', 'data_object_id')
        gfk.contribute_to_class(Activity, 'old_data')

        Place = orm['sa_api_v2.Place']
        Submission = orm['sa_api_v2.Submission']

        for activity in Activity.objects.all():
            try:
                activity.old_data = activity.data.place
            except Place.DoesNotExist:
                activity.old_data = activity.data.submission
            activity.save()

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sa_api_v2.activity': {
            'Meta': {'object_name': 'Activity', 'db_table': "'sa_api_activity'"},
            'action': ('django.db.models.fields.CharField', [], {'default': "'create'", 'max_length': '16'}),
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sa_api_v2.SubmittedThing']"}),
            'data_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'data_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sa_api_v2.place': {
            'Meta': {'object_name': 'Place', '_ormbases': ['sa_api_v2.SubmittedThing']},
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'sa_api_v2.submission': {
            'Meta': {'object_name': 'Submission', '_ormbases': ['sa_api_v2.SubmittedThing']},
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'to': "orm['sa_api_v2.SubmissionSet']"}),
            'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        'sa_api_v2.submissionset': {
            'Meta': {'object_name': 'SubmissionSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submission_sets'", 'to': "orm['sa_api_v2.Place']"}),
            'submission_type': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'sa_api_v2.submittedthing': {
            'Meta': {'object_name': 'SubmittedThing', 'db_table': "'sa_api_submittedthing'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submitter_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sa_api_v2']
    symmetrical = True
