import datetime
import logging
import re
import os.path

from XSConsoleStandard import *
from geppetto.geppettolib import network
from geppetto.geppettolib.network import NetworkConfiguration
from geppetto.geppettolib.puppet import PuppetNode
from geppetto.geppettolib import service
from geppetto.geppettolib.utils import execute
from geppetto.geppettolib.utils import ipinfo
from geppetto.geppettolib import config_generator as gen
from geppetto.geppettolib.network import ValidateIP

log = logging.getLogger('geppetto-console')

REGEX_NETWORK_SETTINGS = {'ip': re.compile(r'.* geppetto_ip=([^ ]+).*'),
                'netmask': re.compile(r'.* geppetto_mask=([^ ]+).*'),
                'gateway': re.compile(r'.* geppetto_gw=([^ ]+).*'),
                'first_ip': re.compile(r'.* geppetto_first_ip=([^ ]+).*'),
                'last_ip': re.compile(r'.* geppetto_last_ip=([^ ]+).*'),
                'hostname': re.compile(r'.* geppetto_hostname=([^ ]+).*'),
                'ntp_server': re.compile(r'.* geppetto_ntp=([^ ]+).*'),
                'dns_suffix': re.compile(r'.* geppetto_dns_suffix=([^ ]+).*')}


class DataUtils:
    #TODO- split this util into meaningful sections?
    instance = None

    def __init__(self):
        self.count = 0
        self.network_config = NetworkConfiguration()
        self.puppet_node = PuppetNode()
        self.geppetto_node = service.GeppettoService()

    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = DataUtils()
        return cls.instance

    def get_all_network_data_for_summary(self):
        network_config = NetworkConfiguration()

        try:
            network_config.load_interface("eth1")
            network_config.load_network()
            network_config.load_dns()
            network_config.load_ntp()

            # TODO build separate ui object that
            # has place holder text for missing info?
            self.puppet_node.load()
            if self.puppet_node.is_master():
                network_config.master_hostname = "%s.%s" % \
                    (network_config.hostname, network_config.dns_suffix)
            else:
                network_config.master_hostname = \
                self.\
                refresh_config_and_generate_puppetmaster_hostname_on_client()

            network_config.admin_url = "http://%s:8080/" % \
                                    network_config.master_hostname
            network_config.is_master = self.is_master()
        except Exception, e:
            log.error(e)

        return network_config

    def is_master(self):
        """Reloads the configuration and returns None if
        unknown or True if master, False if client"""
        try:
            self.puppet_node.load()
            return self.puppet_node.is_master()
        except Exception, e:
            log.error(e)
        return None

    def set_vpx_is_master_choice(self, isMaster):
        """This stores the choice of if the node is the master or not"""
        # TODO... need to do this properly
        if isMaster:
            self.puppet_node.set_node_flag(PuppetNode.MASTER)
        else:
            self.puppet_node.set_node_flag(PuppetNode.PUPPET)

    def is_master_reachable(self):
        """ Refreshes some configuration and
        Returns True if the currently configured master can be reached """
        try:
            masterHostname = self.\
                refresh_config_and_generate_puppetmaster_hostname_on_client()
            log.debug('Contacting master: %s' % masterHostname)
            # use urllib rather than urllib2
            # to ensure that we ignore https errors
            urllib.urlopen('https://%s:8140/production/'
                           'certificate/ca' % masterHostname)
        except:
            return False
        else:
            return True
        return None     # TODO what to return when we can't tell?

    def refresh_config_and_generate_puppetmaster_hostname_on_client(self):
        try:
            self.puppet_node.load()
            master = self.puppet_node.get_puppet_option('server')
            log.debug('Generated master hostname: %s' % master)
            return master
        except:
            log.debug('Failed to generate master hostname.')
            return "master"

    def configure_master_for_external_dhcp(self):
        log.debug('Configuring master with external DHCP')

        self.network_config.load_network()
        if not self.is_crowbar_present():
            self.network_config.set_hostname_and_gateway("master")
        if not self.network_config.is_setup(self.network_config.NETWORK):
            raise Exception("Failed to setup interface.")

        self.network_config.enforce_configuration()

    def set_network_settings(self, host_ip, netmask, hostname, dns_server,
                             dns_suffix, gateway, ntp_server):
        """Update the network settings."""

        log.debug('Setting the network settings: %s %s %s %s %s %s %s' %
                  (host_ip, netmask, hostname, dns_server, dns_suffix,
                   gateway, ntp_server))
        [subnet_address, broadcast_address, reverse_zone_prefix] = \
                                                     ipinfo(host_ip, netmask)
        self.network_config.set_interface("eth1", "static", netmask, host_ip)
        self.network_config.set_network(hostname, dns_suffix, gateway)
        self.network_config.set_dns_server(dns_server, dns_suffix,
                                           reverse_zone_prefix)
        self.network_config.set_ntp_server(ntp_server)
        if not self.network_config.is_setup(self.network_config.INTERFACE) or \
           not self.network_config.is_setup(self.network_config.NETWORK) or \
           not self.network_config.is_setup(self.network_config.DNS) or \
           not self.network_config.is_setup(self.network_config.NTP):
            raise Exception("Failed to setup interface.")

        self.network_config.enforce_configuration()

    def is_ip_address_configured(self):
        """ This refreshes the interface configuration and
        returns True if this VPX has a an IP address from DHCP """
        try:
            self.network_config.load_interface("eth1")
            self.network_config.load_network()
            self.network_config.load_dns()
            if self.network_config.is_setup(self.network_config.INTERFACE):
                return (self.network_config.address != None) and \
                       (self.network_config.address != "") and \
                       (self.network_config.bootproto == "dhcp")
        except Exception, e:
            log.error(e)

        return False

    def make_into_puppet_master(self):
        log.debug('DNS Suffix: %s' % self.network_config.dns_suffix)
        self.geppetto_node.install_service()
        self.geppetto_node.start_service()
        self.puppet_node.\
            set_service_settings({"server-auto-sign-policy": True,
                                  "server-autosign-pattern": "*.%s" % \
                                            self.network_config.dns_suffix, })
        self.puppet_node.\
            set_service_settings({"client-master-reference":
                                    self.network_config.hostname + "." + \
                                            self.network_config.dns_suffix})
        self.puppet_node.install_service()
        self.puppet_node.start_service()

        for _ in xrange(1, 10):
            if self.is_master_reachable():
                break
            time.sleep(6)
        log.debug('Master found, turning itself to a slave.')
        client_node = service.Service('puppet')
        client_node.install_service()
        client_node.start_service()
        self._restart_service('puppet')

        if self.is_crowbar_present():
            base_url = 'http://192.168.124.10:3000/machines/transition/0.yaml'
            self.notify_crowbar_ready(base_url, "vpx-geppettomaster-ready")

    def make_into_puppet_client(self):
        # Note: dhcp client should set the correct master name
        # TODO - prompt for master name when dhcp fails to provide the name?
        self.set_vpx_is_master_choice(False)
        self._test_dns()
        self.puppet_node.install_service()
        self.puppet_node.start_service()

        if self.is_crowbar_present():
            self.notify_crowbar_ready("vpx-geppettoclient-ready")

    def start_dns_dhcp(self, ip_address, subnet_mask, dns_suffix,
                       first_ip, last_ip, puppet_master):
        [subnet_address, broadcast_address, reverse_zone_prefix] = \
                                        ipinfo(ip_address, subnet_mask)
        config_map = {'hostname': puppet_master,
                      'interface': ip_address,
                      'dhcp_server': ip_address,
                      'subnet': subnet_address,
                      'subnet_mask': subnet_mask,
                      'broadcast_address': broadcast_address,
                      'routers': ip_address,
                      'domain_name_servers': ip_address,
                      'dns_suffix': dns_suffix,
                      'range_from': first_ip,
                      'range_to': last_ip,
                      'nic': 'eth1',
                      'reverse_zone_prefix': reverse_zone_prefix,
                      'dns_server': ip_address,
                      'puppet_master': puppet_master, }

        config = {gen.NAMED_CONF_TEMPLATE_FILE: '/etc/named.conf',
                  gen.NAMED_FORWARD_ZONE_TEMPLATE_FILE: '/var/named/zone.%s' \
                                                % config_map['dns_suffix'],
                  gen.NAMED_REVERSE_ZONE_TEMPLATE_FILE: '/var/named/%s.zone' \
                                        % config_map['reverse_zone_prefix'],
                  gen.DHCPD_CONF_TEMPLATE_FILE:
                                            '/usr/share/geppetto/dhcpd.conf',
                  gen.DHCPD_ARGS_TEMPLATE_FILE: '/usr/share/geppetto/dhcpd',
                  gen.RESLV_TEMPLATE_FILE: '/usr/share/geppetto/resolv.conf', }

        for (template_file, config_file) in config.items():
            gen.write_config(gen.fill_template(template_file, config_map),
                             config_file)

        execute("/usr/local/bin/geppetto/rndckeygen.sh")
        self._restart_service("named")
        self._restart_service("dhcpd")

    def validate_master_network_settings(self, values):
        ValidateIP.ensure_valid_address(values["ip"], "ip address")
        ValidateIP.ensure_valid_mask(mask=values["netmask"])
        ValidateIP.ensure_valid_address(values["gateway"], "gateway")
        ValidateIP.ensure_valid_address(values["ntp_server"], "ntp_server")
        ValidateIP.ensure_valid_address(values["first_ip"], "first_ip address")
        ValidateIP.ensure_valid_address(values["last_ip"], "last_ip address")

        ValidateIP.ensure_valid_hostname(values["hostname"], "hostname")
        ValidateIP.ensure_valid_dns_suffix(values["dns_suffix"], "dns_suffix")

        ValidateIP.ensure_ip_in_network(address=values["ip"],
                mask=values["netmask"],
                check_address=values["first_ip"],
                setting="first_ip")
        ValidateIP.ensure_ip_in_network(address=values["ip"],
                mask=values["netmask"],
                check_address=values["last_ip"],
                setting="last_ip")
        ValidateIP.is_last_ip_less_than_first(first_ip=values["first_ip"],
                last_ip=values["last_ip"])

    def restart_network(self):
        self._execute("service", "network", "restart")

    def get_ip_settings_from_kernel_args(self):
        """
        It will return a list of ip, mask, gw, hostname, dns, ntp, first_ip,
        last_ip from kernel args in '/proc/cmdline'. It doesn't do any kind of
        validation for which _kernel_option_specify_network_settings should be
        used.
        """
        cmdline = self.get_kernel_cmdline()
        values = {}
        for x in REGEX_NETWORK_SETTINGS:
            if REGEX_NETWORK_SETTINGS[x].match(cmdline):
                values[x] = \
                    (REGEX_NETWORK_SETTINGS[x].match(cmdline)).groups()[0]
            else:
                values[x] = ''
        return values

    def _restart_service(self, service):
        self._execute("chkconfig", service, "on")
        self._execute("service", service, "restart")

    def _execute(self, command, service, action):
        execute('%s %s %s' % (command, service, action))

    def _kernel_option_specify_network_settings(self):
        """This function will return None if there are no ip settings in
        cmdline. It returns False if the ip values are present in
        cmdline but are invalid. It will return a list of ip, mask,
        gw, hostname, dns, ntp, first_ip, last_ip if the values are valid."""
        cmdline = self.get_kernel_cmdline()
        if not (('geppetto_ip=' in cmdline) and
                ('geppetto_mask=' in cmdline) and
                ('geppetto_first_ip=' in cmdline) and
                ('geppetto_last_ip=' in cmdline) and
                ('geppetto_hostname=' in cmdline) and
                ('geppetto_dns_suffix=' in cmdline)):
            return None
        values = self.get_ip_settings_from_kernel_args()
        try:
            self.validate_master_network_settings(values)
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(\
                Lang('Network settings from kernel Failed: ') + Lang(e) + \
                     '\n Starting DHCP server ...'))
            return False
        return True

    def _test_dns(self):
        """This tests that the host has a fqdn.
        FQDN is essential in the registration process with a puppet master.
        """
        MAX_TRIES = 35
        hostname = ''
        for x in xrange(1, MAX_TRIES + 1):
            try:
                hostname = network.get_hostname()
                if hostname.find('.') == -1:
                    log.debug('No FQDN available yet(%s): sleeping for %d sec',
                              hostname, x)
                    log.debug('It is %s', str(datetime.datetime.now()))
                    time.sleep(x)
                else:
                    log.debug('Found fqdn(%s) after: %d seconds', hostname,
                              x > 1 and x * (x + 1) / 2 or 0)
                    return
            except:
                log.error('DNS Lookup failed: sleeping for %d sec!' % x)
                time.sleep(x)
        log.error('DNS lookup failed after %d trials. Bailing!' % MAX_TRIES)
        # If we get here, it's most likely that the DDNS registration
        # has failed. This is most likely because the RRSET add
        # operation has timed out leaving named with a PTR record
        # of the VPX in question and dhcpd believing that
        # it still needs to add one. Successive dhcp renewals will
        # fail, and Puppet will never work. Only way to recover from
        # this is to manually remove the PTR from named's zone file.
        raise Exception('DNS lookup/registration failed: unable to '
                        'register with master, please contact the '
                        'administrator')

    def notify_crowbar_ready(self, base_url, state):
        try:
            mac = "`ifconfig eth1 | grep HWaddr | awk '{ print \$5 }'`"
            cmd = """wget -q "%s?mac=%s&state=%s" -O- -T 30"""
            execute(cmd % (base_url, mac, state))
        except Exception, e:
            log.error(e)

    def get_kernel_cmdline(self):
        # First check if there is a file /var/lib/geppetto/esx_kernel_cmd_line
        # If it's present, this VPX is on ESX and will have the complete
        # command line (including the contents of /proc/cmdline) so just read
        # that and return its contents. Else, just return whatever is
        # present in /proc/cmdline (for XS). BTW, we prepare this
        # esx_kernel_cmd file in the 77-vmtools-info script
        if os.path.isfile('/var/lib/geppetto/esx_kernel_cmd_line'):
            with file('/var/lib/geppetto/esx_kernel_cmd_line') as f:
                return f.readline().strip()
        else:
            with file('/proc/cmdline') as f:
                return f.readline().strip()

    def is_crowbar_present(self):
        return self.get_kernel_cmdline().find("crowbar=true") != -1
