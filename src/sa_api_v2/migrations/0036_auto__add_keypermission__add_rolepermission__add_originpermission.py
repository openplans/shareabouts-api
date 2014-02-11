# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ('sa_api_v2.cors', '0004__rename_originpermission_to_origin.py'),
    )

    def forwards(self, orm):
        # Adding model 'KeyPermission'
        db.create_table(u'sa_api_v2_keypermission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('can_create', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_update', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_destroy', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('submission_set', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('key', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['apikey.ApiKey'])),
        ))
        db.send_create_signal(u'sa_api_v2', ['KeyPermission'])

        # Adding model 'RolePermission'
        db.create_table(u'sa_api_v2_rolepermission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('can_create', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_update', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_destroy', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('submission_set', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sa_api_v2.Role'])),
        ))
        db.send_create_signal(u'sa_api_v2', ['RolePermission'])

        # Adding model 'OriginPermission'
        db.create_table(u'sa_api_v2_originpermission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('can_create', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_update', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('can_destroy', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('submission_set', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cors.Origin'])),
        ))
        db.send_create_signal(u'sa_api_v2', ['OriginPermission'])


    def backwards(self, orm):
        # Deleting model 'KeyPermission'
        db.delete_table(u'sa_api_v2_keypermission')

        # Deleting model 'RolePermission'
        db.delete_table(u'sa_api_v2_rolepermission')

        # Deleting model 'OriginPermission'
        db.delete_table(u'sa_api_v2_originpermission')


    models = {
        u'apikey.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'keys'", 'blank': 'True', 'to': u"orm['sa_api_v2.DataSet']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'last_used': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'logged_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
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
        u'cors.origin': {
            'Meta': {'object_name': 'Origin'},
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'origins'", 'blank': 'True', 'to': u"orm['sa_api_v2.DataSet']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_used': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'logged_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'pattern': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sa_api_v2.action': {
            'Meta': {'ordering': "['-created_datetime']", 'object_name': 'Action', 'db_table': "'sa_api_activity'"},
            'action': ('django.db.models.fields.CharField', [], {'default': "'create'", 'max_length': '16'}),
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actions'", 'db_column': "'data_id'", 'to': u"orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sa_api_v2.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'sa_api_attachment'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'thing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': u"orm['sa_api_v2.SubmittedThing']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sa_api_v2.dataset': {
            'Meta': {'unique_together': "(('owner', 'slug'),)", 'object_name': 'DataSet', 'db_table': "'sa_api_dataset'"},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "u''", 'max_length': '128'})
        },
        u'sa_api_v2.keypermission': {
            'Meta': {'object_name': 'KeyPermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['apikey.ApiKey']"}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        u'sa_api_v2.originpermission': {
            'Meta': {'object_name': 'OriginPermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cors.Origin']"}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        u'sa_api_v2.place': {
            'Meta': {'ordering': "['-updated_datetime']", 'object_name': 'Place', 'db_table': "'sa_api_place'", '_ormbases': [u'sa_api_v2.SubmittedThing']},
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            u'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'sa_api_v2.role': {
            'Meta': {'unique_together': "[('name', 'dataset')]", 'object_name': 'Role', 'db_table': "'sa_api_role'"},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sa_api_v2.DataSet']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'submitters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'roles'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        u'sa_api_v2.rolepermission': {
            'Meta': {'object_name': 'RolePermission'},
            'can_create': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_destroy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_update': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sa_api_v2.Role']"}),
            'submission_set': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        u'sa_api_v2.submission': {
            'Meta': {'ordering': "['-updated_datetime']", 'object_name': 'Submission', 'db_table': "'sa_api_submission'", '_ormbases': [u'sa_api_v2.SubmittedThing']},
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'to': u"orm['sa_api_v2.SubmissionSet']"}),
            u'submittedthing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sa_api_v2.SubmittedThing']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'sa_api_v2.submissionset': {
            'Meta': {'unique_together': "(('place', 'name'),)", 'object_name': 'SubmissionSet', 'db_table': "'sa_api_submissionset'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submission_sets'", 'to': u"orm['sa_api_v2.Place']"})
        },
        u'sa_api_v2.submittedthing': {
            'Meta': {'object_name': 'SubmittedThing', 'db_table': "'sa_api_submittedthing'"},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'things'", 'blank': 'True', 'to': u"orm['sa_api_v2.DataSet']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'things'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'updated_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['sa_api_v2']