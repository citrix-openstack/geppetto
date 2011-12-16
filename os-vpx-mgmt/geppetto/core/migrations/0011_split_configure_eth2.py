# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        # Change class configure-eth2 ==> configure-public-vif
        configure_eth2 = orm.ConfigClass.objects.get(id='13')
        configure_eth2.name = 'configure-public-vif'
        configure_eth2.description = 'Controls the configuration for the VPX public network interface stored in /etc/sysconfig/network-scripts/ifcfg-ethX (i.e. eth2).'
        configure_eth2.save()
        bridge_interface = orm.ConfigClassParameter.objects.get(id='43')
        bridge_interface.default_value = 'eth2'
        bridge_interface.save() 
        # Change param ETH2_HOST_NETWORK ==> PUBLIC_NETWORK_BRIDGE
        # NOTE(salvatore): the NO_NET default value could be removed now
        eth2_host_network = orm.ConfigClassParameter.objects.get(id='48')
        eth2_host_network.name = 'PUBLIC_NETWORK_BRIDGE'
        eth2_host_network.default_value = 'NO_NET'
        eth2_host_network.save()
        # Change param ETH2_IP ==> PUBLIC_NW_VIF_IP
        eth2_ip = orm.ConfigClassParameter.objects.get(id='31')
        eth2_ip.name = 'PUBLIC_NW_VIF_IP'
        eth2_ip.save()
        # Change param ETH2_MODE ==> PUBLIC_NW_VIF_MODE
        eth2_mode = orm.ConfigClassParameter.objects.get(id='25')
        eth2_mode.name = 'PUBLIC_NW_VIF_MODE'
        eth2_mode.save()
        # Change param ETH2_NETMASK ==> PUBLIC_NW_VIF_NETMASK
        eth2_netmask = orm.ConfigClassParameter.objects.get(id='32')
        eth2_netmask.name = 'PUBLIC_NW_VIF_NETMASK'
        eth2_netmask.save()
        # Add param PUBLIC_INTERFACE
        orm.ConfigClassParameter.objects.create(name='PUBLIC_INTERFACE',
                                                config_class=configure_eth2,
                                                description='The VPX interface to use for public traffic.',
                                                default_value='eth2',
                                                config_type=None)
        # Add class configure-guest-nw-vif
        configure_guest_vif = orm.ConfigClass.objects.create(name='configure-guest-nw-vif',
                                                             description='Controls the configuration for the VPX Network Worker.')
        # Add param GUEST_NW_VIF_MODE => configure-guest-nw-vif
        onboot_type = orm.ConfigClassParameterType.objects.get(id='12')
        orm.ConfigClassParameter.objects.create(name='GUEST_NW_VIF_MODE',
                                                config_class=configure_guest_vif,
                                                description='Configuration mode.',
                                                default_value='noip',
                                                config_type=onboot_type)
        # Add param GUEST_NW_VIF_IP => configure-guest-nw-vif
        ipaddress_type = orm.ConfigClassParameterType.objects.get(id='3')
        orm.ConfigClassParameter.objects.create(name='GUEST_NW_VIF_IP',
                                                config_class=configure_guest_vif,
                                                description='Static IP address for the interface.',
                                                default_value='noip',
                                                config_type=ipaddress_type)
        # Add param GUEST_NW_VIF_NETMASK => configure-guest-nw-vif
        orm.ConfigClassParameter.objects.create(name='GUEST_NW_VIF_NETMASK',
                                                config_class=configure_guest_vif,
                                                description='Netmask for the interface.',
                                                default_value='255.255.255.0',
                                                config_type=ipaddress_type)
        # Add role
        network_role = orm.Role.objects.get(id='3')
        orm.RoleConfigClassAssignment.objects.create(role=network_role,
                                                     config_class=configure_guest_vif)

    def backwards(self, orm):
        raise NotImplementedError()


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
            'description': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.RoleDescription']", 'null': 'True', 'blank': 'True'}),
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
        },
        'core.roledesconfigparamassignment': {
            'Meta': {'ordering': "['role_description']", 'unique_together': "(('config_parameter', 'role_description'),)", 'object_name': 'RoleDesConfigParamAssignment'},
            'config_parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ConfigClassParameter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role_description': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.RoleDescription']"})
        },
        'core.roledescription': {
            'Meta': {'ordering': "['name']", 'object_name': 'RoleDescription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'})
        }
    }

    complete_apps = ['core']
