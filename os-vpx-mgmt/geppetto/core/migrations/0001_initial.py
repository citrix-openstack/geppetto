# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from geppetto.core.migrations import load_data

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'ConfigClass'
        db.create_table('core_configclass', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('core', ['ConfigClass'])

        # Adding model 'ConfigClassParameterType'
        db.create_table('core_configclassparametertype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('validator_function', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('validator_kwargs', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['ConfigClassParameterType'])

        # Adding model 'ConfigClassParameter'
        db.create_table('core_configclassparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('config_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ConfigClass'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('config_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ConfigClassParameterType'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('core', ['ConfigClassParameter'])

        # Adding model 'Role'
        db.create_table('core_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, db_index=True)),
            ('service', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('internal', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['Role'])

        # Adding model 'RoleConfigClassAssignment'
        db.create_table('core_roleconfigclassassignement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Role'])),
            ('config_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ConfigClass'])),
        ))
        db.send_create_signal('core', ['RoleConfigClassAssignment'])

        # Adding unique constraint on 'RoleConfigClassAssignment', fields ['role', 'config_class']
        db.create_unique('core_roleconfigclassassignement', ['role_id', 'config_class_id'])

        # Adding model 'Host'
        db.create_table('core_host', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fqdn', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, db_index=True)),
            ('address', self.gf('django.db.models.fields.IPAddressField')(max_length=15, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
        ))
        db.send_create_signal('core', ['Host'])

        # Adding model 'Group'
        db.create_table('core_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, db_index=True)),
        ))
        db.send_create_signal('core', ['Group'])

        # Adding model 'Master'
        db.create_table('core_master', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fqdn', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, db_index=True)),
            ('promoted_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['Master'])

        # Adding model 'Node'
        db.create_table('core_node', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fqdn', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, db_index=True)),
            ('joined_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('master', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Master'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Group'], null=True, blank=True)),
            ('facts', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('report', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('facts_list', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('report_log', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('report_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('report_last_changed_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('report_status', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Host'], null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Node'])

        # Adding model 'NodeRoleAssignment'
        db.create_table('core_noderoleassignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Node'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Role'])),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['NodeRoleAssignment'])

        # Adding unique constraint on 'NodeRoleAssignment', fields ['role', 'node']
        db.create_unique('core_noderoleassignment', ['role_id', 'node_id'])

        # Adding model 'Override'
        db.create_table('core_override', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Node'])),
            ('config_class_parameter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ConfigClassParameter'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('one_time_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['Override'])

        # Adding unique constraint on 'Override', fields ['node', 'config_class_parameter']
        db.create_unique('core_override', ['node_id', 'config_class_parameter_id'])

        # Adding model 'GroupOverride'
        db.create_table('core_groupoverride', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Group'])),
            ('config_class_parameter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ConfigClassParameter'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('core', ['GroupOverride'])

        # Adding unique constraint on 'GroupOverride', fields ['group', 'config_class_parameter']
        db.create_unique('core_groupoverride', ['group_id', 'config_class_parameter_id'])

        # load the date
        load_data(orm, 'migrations_0001_initial')


    def backwards(self, orm):

        raise NotImplemented() # there is no easy way to unload the data

        # Removing unique constraint on 'GroupOverride', fields ['group', 'config_class_parameter']
        db.delete_unique('core_groupoverride', ['group_id', 'config_class_parameter_id'])

        # Removing unique constraint on 'Override', fields ['node', 'config_class_parameter']
        db.delete_unique('core_override', ['node_id', 'config_class_parameter_id'])

        # Removing unique constraint on 'NodeRoleAssignment', fields ['role', 'node']
        db.delete_unique('core_noderoleassignment', ['role_id', 'node_id'])

        # Removing unique constraint on 'RoleConfigClassAssignment', fields ['role', 'config_class']
        db.delete_unique('core_roleconfigclassassignement', ['role_id', 'config_class_id'])

        # Deleting model 'ConfigClass'
        db.delete_table('core_configclass')

        # Deleting model 'ConfigClassParameterType'
        db.delete_table('core_configclassparametertype')

        # Deleting model 'ConfigClassParameter'
        db.delete_table('core_configclassparameter')

        # Deleting model 'Role'
        db.delete_table('core_role')

        # Deleting model 'RoleConfigClassAssignment'
        db.delete_table('core_roleconfigclassassignement')

        # Deleting model 'Host'
        db.delete_table('core_host')

        # Deleting model 'Group'
        db.delete_table('core_group')

        # Deleting model 'Master'
        db.delete_table('core_master')

        # Deleting model 'Node'
        db.delete_table('core_node')

        # Deleting model 'NodeRoleAssignment'
        db.delete_table('core_noderoleassignment')

        # Deleting model 'Override'
        db.delete_table('core_override')

        # Deleting model 'GroupOverride'
        db.delete_table('core_groupoverride')


    models = {
        'core.configclass': {
            'Meta': {'ordering': "['name']", 'object_name': 'ConfigClass'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'core.configclassparameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'ConfigClassParameter'},
            'config_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ConfigClass']"}),
            'config_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ConfigClassParameterType']", 'null': 'True', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'core.configclassparametertype': {
            'Meta': {'ordering': "['name']", 'object_name': 'ConfigClassParameterType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'validator_function': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'validator_kwargs': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'core.group': {
            'Meta': {'ordering': "['name']", 'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'})
        },
        'core.groupoverride': {
            'Meta': {'ordering': "['group']", 'unique_together': "(('group', 'config_class_parameter'),)", 'object_name': 'GroupOverride'},
            'config_class_parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ConfigClassParameter']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'core.host': {
            'Meta': {'ordering': "['fqdn']", 'object_name': 'Host'},
            'address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'blank': 'True'}),
            'fqdn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'})
        },
        'core.master': {
            'Meta': {'ordering': "['fqdn']", 'object_name': 'Master'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fqdn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'promoted_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'core.node': {
            'Meta': {'ordering': "['fqdn']", 'object_name': 'Node'},
            'facts': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'facts_list': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fqdn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']", 'null': 'True', 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Host']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'joined_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Master']"}),
            'report': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'report_last_changed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'report_log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'report_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Role']", 'through': "orm['core.NodeRoleAssignment']", 'symmetrical': 'False'})
        },
        'core.noderoleassignment': {
            'Meta': {'ordering': "['node']", 'unique_together': "(('role', 'node'),)", 'object_name': 'NodeRoleAssignment'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Node']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Role']"})
        },
        'core.override': {
            'Meta': {'ordering': "['node']", 'unique_together': "(('node', 'config_class_parameter'),)", 'object_name': 'Override'},
            'config_class_parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ConfigClassParameter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Node']"}),
            'one_time_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'core.role': {
            'Meta': {'ordering': "['name']", 'object_name': 'Role'},
            'config_classes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.ConfigClass']", 'through': "orm['core.RoleConfigClassAssignment']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'service': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'core.roleconfigclassassignment': {
            'Meta': {'ordering': "['role']", 'unique_together': "(('role', 'config_class'),)", 'object_name': 'RoleConfigClassAssignment', 'db_table': "'core_roleconfigclassassignement'"},
            'config_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ConfigClass']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Role']"})
        }
    }

    complete_apps = ['core']
