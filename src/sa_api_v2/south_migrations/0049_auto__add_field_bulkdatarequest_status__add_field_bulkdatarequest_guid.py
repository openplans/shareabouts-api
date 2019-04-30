# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BulkDataRequest.status'
        db.add_column('sa_api_bulkdatarequest', 'status',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'BulkDataRequest.guid'
        db.add_column('sa_api_bulkdatarequest', 'guid',
                      self.gf('django.db.models.fields.TextField')(default='', unique=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BulkDataRequest.status'
        db.delete_column('sa_api_bulkdatarequest', 'status')

        # Deleting field 'BulkDataRequest.guid'
        db.delete_column('sa_api_bulkdatarequest', 'guid')


    models = {
        'apikey.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keys'", 'blank': 'True', 'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "'M2FjMmUwMmEyNzk2OGNiYzc4NzAwMjUx'", 'unique': 'True', 'max_length': '32'}),
            'last_used': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'logged_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'cors.origin': {
            'Meta': {'object_name': 'Origin'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'origins'", 'blank': 'True', 'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_used': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'logged_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'pattern': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sa_api_v2.action': {
            'Meta': {'ordering': "['-created_datetime']", 'object_name': 'Action', 'db_table': "'sa_api_activity'"},
            'action': ('django.db.models.fields.CharField', [], {'default': "'create'", 'max_length': '16'}),
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actions'", 'db_column': "'data_id'", 'to': "orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'sa_api_v2.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'sa_api_attachment'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'sa_api_v2.bulkdata': {
            'Meta': {'object_name': 'BulkData', 'db_table': "'sa_api_bulkdata'"},
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'fulfillment'", 'unique': 'True', 'null': 'True', 'to': "orm['sa_api_v2.BulkDataRequest']"})
        },
        'sa_api_v2.bulkdatarequest': {
            'Meta': {'object_name': 'BulkDataRequest', 'db_table': "'sa_api_bulkdatarequest'"},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sa_api_v2.DataSet']"}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'fulfilled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'guid': ('django.db.models.fields.TextField', [], {'default': "''", 'unique': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_invisible': ('django.db.models.fields.BooleanField', [], {}),
            'include_private': ('django.db.models.fields.BooleanField', [], {}),
            'include_submissions': ('django.db.models.fields.BooleanField', [], {}),
            'requested_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'requester': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sa_api_v2.User']", 'null': 'True'}),
            'status': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'sa_api_v2.dataindex': {
            'Meta': {'object_name': 'DataIndex'},
            'attr_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'attr_type': ('django.db.models.fields.CharField', [], {'default': "'string'", 'max_length': '10'}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'indexes'", 'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'sa_api_v2.dataset': {
            'Meta': {'unique_together': "(('owner', 'slug'),)", 'object_name': 'DataSet', 'db_table': "'sa_api_dataset'"},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': "orm['sa_api_v2.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "u''", 'max_length': '128'})
        },
        'sa_api_v2.datasetpermission': {
            'Meta': {'object_name': 'DataSetPermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_retrieve': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'blank': 'True'}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'sa_api_v2.group': {
            'Meta': {'unique_together': "[('name', 'dataset')]", 'object_name': 'Group', 'db_table': "'sa_api_group'"},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'submitters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'_groups'", 'blank': 'True', 'to': "orm['sa_api_v2.User']"})
        },
        'sa_api_v2.grouppermission': {
            'Meta': {'object_name': 'GroupPermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_retrieve': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['sa_api_v2.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'blank': 'True'}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'sa_api_v2.indexedvalue': {
            'Meta': {'object_name': 'IndexedValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'values'", 'to': "orm['sa_api_v2.DataIndex']"}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'indexed_values'", 'to': "orm['sa_api_v2.SubmittedThing']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'})
        },
        'sa_api_v2.keypermission': {
            'Meta': {'object_name': 'KeyPermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_retrieve': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['apikey.ApiKey']"}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'blank': 'True'}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'sa_api_v2.originpermission': {
            'Meta': {'object_name': 'OriginPermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_retrieve': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['cors.Origin']"}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'blank': 'True'}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'sa_api_v2.place': {
            'Meta': {'ordering': "['-updated_datetime']", 'object_name': 'Place', 'db_table': "'sa_api_place'", '_ormbases': ['sa_api_v2.SubmittedThing']},
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        'sa_api_v2.submission': {
            'Meta': {'ordering': "['-updated_datetime']", 'object_name': 'Submission', 'db_table': "'sa_api_submission'", '_ormbases': ['sa_api_v2.SubmittedThing']},
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'to': "orm['sa_api_v2.SubmissionSet']"}),
            'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        'sa_api_v2.submissionset': {
            'Meta': {'unique_together': "(('place', 'name'),)", 'object_name': 'SubmissionSet', 'db_table': "'sa_api_submissionset'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submission_sets'", 'to': "orm['sa_api_v2.Place']"})
        },
        'sa_api_v2.submittedthing': {
            'Meta': {'object_name': 'SubmittedThing', 'db_table': "'sa_api_submittedthing'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'things'", 'blank': 'True', 'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'things'", 'null': 'True', 'to': "orm['sa_api_v2.User']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'})
        },
        'sa_api_v2.user': {
            'Meta': {'object_name': 'User', 'db_table': "'auth_user'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'sa_api_v2.webhook': {
            'Meta': {'object_name': 'Webhook', 'db_table': "'sa_api_webhook'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True', 'blank': 'True'}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'webhooks'", 'to': "orm['sa_api_v2.DataSet']"}),
            'event': ('django.db.models.fields.CharField', [], {'default': "'add'", 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2048'})
        }
    }

    complete_apps = ['sa_api_v2']