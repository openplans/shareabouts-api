# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Group'
        db.create_table('sa_api_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sa_api_v2.DataSet'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('sa_api_v2', ['Group'])

        # Adding M2M table for field submitters on 'Group'
        m2m_table_name = db.shorten_name('sa_api_group_submitters')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['sa_api_v2.group'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'user_id'])

        # Adding unique constraint on 'Group', fields ['name', 'dataset']
        db.create_unique('sa_api_group', ['name', 'dataset_id'])


        # Changing field 'Action.created_datetime'
        db.alter_column('sa_api_activity', 'created_datetime', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'SubmittedThing.created_datetime'
        db.alter_column('sa_api_submittedthing', 'created_datetime', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Attachment.created_datetime'
        db.alter_column('sa_api_attachment', 'created_datetime', self.gf('django.db.models.fields.DateTimeField')())

    def backwards(self, orm):
        # Removing unique constraint on 'Group', fields ['name', 'dataset']
        db.delete_unique('sa_api_group', ['name', 'dataset_id'])

        # Deleting model 'Group'
        db.delete_table('sa_api_group')

        # Removing M2M table for field submitters on 'Group'
        db.delete_table(db.shorten_name('sa_api_group_submitters'))


        # Changing field 'Action.created_datetime'
        db.alter_column('sa_api_activity', 'created_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'SubmittedThing.created_datetime'
        db.alter_column('sa_api_submittedthing', 'created_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Attachment.created_datetime'
        db.alter_column('sa_api_attachment', 'created_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
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
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sa_api_v2.action': {
            'Meta': {'ordering': "['-created_datetime']", 'object_name': 'Action', 'db_table': "'sa_api_activity'"},
            'action': ('django.db.models.fields.CharField', [], {'default': "'create'", 'max_length': '16'}),
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actions'", 'db_column': "'data_id'", 'to': "orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sa_api_v2.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'sa_api_attachment'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sa_api_v2.dataset': {
            'Meta': {'unique_together': "(('owner', 'slug'),)", 'object_name': 'DataSet', 'db_table': "'sa_api_dataset'"},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "u''", 'max_length': '128'})
        },
        'sa_api_v2.place': {
            'Meta': {'ordering': "['-updated_datetime']", 'object_name': 'Place', 'db_table': "'sa_api_place'", '_ormbases': ['sa_api_v2.SubmittedThing']},
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        'sa_api_v2.group': {
            'Meta': {'unique_together': "[('name', 'dataset')]", 'object_name': 'Group', 'db_table': "'sa_api_group'"},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'submitters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groups'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
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
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'things'", 'blank': 'True', 'to': "orm['sa_api_v2.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'things'", 'null': 'True', 'to': "orm['auth.User']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['sa_api_v2']