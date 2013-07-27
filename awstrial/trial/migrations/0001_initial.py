# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'UserProfile'
        db.create_table('trial_userprofile', (
            ('opt_marketing', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('has_ssh', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('trial', ['UserProfile'])

        # Adding model 'EmailBlacklist'
        db.create_table('trial_emailblacklist', (
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('trial', ['EmailBlacklist'])

        # Adding model 'Campaign'
        db.create_table('trial_campaign', (
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('max_instances', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
        ))
        db.send_create_signal('trial', ['Campaign'])

        # Adding model 'Instances'
        db.create_table('trial_instances', (
            ('ami_id', self.gf('django.db.models.fields.SlugField')(max_length=12)),
            ('terminated_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trial.Campaign'])),
            ('shutdown_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('ph_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('instance_id', self.gf('django.db.models.fields.SlugField')(max_length=10, db_index=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('console_start', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('reservation_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('pubkeys', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('config_info', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('console_end', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('running_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('trial', ['Instances'])

        # Adding model 'Feedback'
        db.create_table('trial_feedback', (
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('trial', ['Feedback'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'UserProfile'
        db.delete_table('trial_userprofile')

        # Deleting model 'EmailBlacklist'
        db.delete_table('trial_emailblacklist')

        # Deleting model 'Campaign'
        db.delete_table('trial_campaign')

        # Deleting model 'Instances'
        db.delete_table('trial_instances')

        # Deleting model 'Feedback'
        db.delete_table('trial_feedback')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trial.campaign': {
            'Meta': {'object_name': 'Campaign'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_instances': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'trial.emailblacklist': {
            'Meta': {'object_name': 'EmailBlacklist'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'trial.feedback': {
            'Meta': {'object_name': 'Feedback'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'trial.instances': {
            'Meta': {'object_name': 'Instances'},
            'ami_id': ('django.db.models.fields.SlugField', [], {'max_length': '12'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trial.Campaign']"}),
            'config_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'console_end': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'console_start': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_id': ('django.db.models.fields.SlugField', [], {'max_length': '10', 'db_index': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'ph_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'pubkeys': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'reservation_time': ('django.db.models.fields.DateTimeField', [], {}),
            'running_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'shutdown_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'terminated_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'trial.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'has_ssh': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opt_marketing': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }
    
    complete_apps = ['trial']
