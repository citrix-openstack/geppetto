import logging
from django import forms
from geppetto.geppettolib.utils import execute
from geppetto.geppettolib.utils import quote
from geppetto.hapi import config_util

logger = logging.getLogger('geppetto.ui.forms')


class SwiftHashPathSuffixForm(forms.Form):
    hash_path_suffix = forms.CharField(label="Hash Path Suffix")


class SwiftStorageSizeForm(forms.Form):
    size = forms.IntegerField(label="Disk Size (GB):")


class PasswordForm(forms.Form):
    password = forms.CharField(label="Password:", widget=forms.PasswordInput)
    repeat_password = forms.CharField(label="Repeat Password:",
                                      widget=forms.PasswordInput)
    _validator = '/usr/local/bin/geppetto/os-vpx/hapi-check --test'

    def clean(self):
        if self.is_valid():
            password1 = self.cleaned_data["password"]
            password2 = self.cleaned_data["repeat_password"]
            if password1 != password2:
                raise forms.ValidationError("The passwords must match.")
            if not self._is_valid_hypervisor_pwd():
                raise forms.ValidationError(
                    "Password is invalid. Please, check that the hypervisor "
                    "password is correct.")
        return self.cleaned_data

    def _is_valid_hypervisor_pwd(self):
        try:
            logger.debug('Password check: validating...')
            execute('%s %s %s' % (PasswordForm._validator,
                                  'root',
                                  quote(self.cleaned_data["password"])))
            logger.debug('Password check: succeded')
        except Exception, e:
            logger.debug('Password check: failure')
            logger.error(e)
            return False
        return True


class ChooseWorkerForm(forms.Form):
    worker = forms.ChoiceField(choices=(("test", "test"), ("test2", "test2")))

    def add_workers_into_form(self, workers):
        node_fqdns = workers.keys()
        node_fqdns.sort()
        choices = [generate_choice_entry(node_fqdn, workers[node_fqdn]) \
                                                  for node_fqdn in node_fqdns]
        self.fields["worker"].choices = \
            [("", "Please select a server...")] + choices

    def add_workers_into_form_plus_external(self, workers):
        node_fqdns = workers.keys()
        node_fqdns.sort()
        choices = [generate_choice_entry(node_fqdn, workers[node_fqdn]) \
                                                  for node_fqdn in node_fqdns]
        self.fields["worker"].choices = \
            [("", "Please select a server...")] + choices + \
            [("external", "External System")]

    def get_clean_worker(self):
        return self.cleaned_data["worker"]


class ReadOnlyWorker(forms.Form):
    worker = forms.CharField(widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))

    def update_worker(self, worker):
        self.fields["worker"].initial = worker


class SetupMySQL(ChooseWorkerForm):
    password = forms.CharField(label="Root Password:",
                               widget=forms.PasswordInput)


class SetupNetwork(forms.Form):

    networking_mode = forms.ChoiceField(choices=(("flat", "Flat networking"),
                                                 ("flatdhcp",
                                                  "Flat networking with DHCP"),
                                                 ("vlan", "vLAN networking")),
                                        initial="flat",
                                        label="Select networking mode:",
                                        widget=forms.RadioSelect)
    #TODO: Give us the real initial value here!!!
    multi_host = forms.BooleanField(initial=False,
                                     label="Enable HA networking",
                                     required=False)


class SetupGlance(ChooseWorkerForm):
    default_storage = \
        forms.ChoiceField(choices=(("file", "File System"),
                                   ("swift", "Swift Object Store")),
                          initial="filesystem", widget=forms.RadioSelect)
    extra_data = \
        forms.CharField(label="Additional Disk Size (GB):",
                        widget=forms.TextInput(
                            attrs={'class': 'change-label',
                                   'id_default_storage_0':
                                   'Additional Disk Size (GB):',
                                   'id_default_storage_0_data': '',
                                   'id_default_storage_1':
                                   'Swift Auth Hostname:',
                                   'id_default_storage_1_data': ''}))

    def update_swift_api_hostname(self, hostname):
        self.fields["extra_data"].widget.attrs[
            "id_default_storage_1_data"] = hostname

    def clean_extra_data(self):
        extra_data = self.cleaned_data["extra_data"]
        default_storage = self.cleaned_data["default_storage"]
        if default_storage == "file":
            try:
                float(extra_data)
            except:
                raise forms.ValidationError("Please specify a valid number.")
        return extra_data


class MultipleChoiceWorkerForm(forms.Form):
    workers = forms.MultipleChoiceField(choices=(("test", "test"),
                                                 ("test2", "test2")))

    def add_workers_into_form(self, workers):
        node_fqdns = workers.keys()
        node_fqdns.sort()
        choices = [generate_choice_entry(node_fqdn, workers[node_fqdn]) \
                                                  for node_fqdn in node_fqdns]

        self.fields["workers"].choices = choices

    def clean_workers(self):
        workers = self.cleaned_data["workers"]
        if len(workers) < 3:
            raise forms.ValidationError(
                "You must specify at least three workers.")
        return workers


class _ChooseNetwork(forms.Form):
    network_hint = "%s or %s" % (\
                      config_util.HYPERVISOR.XEN_API_DEFAULT_PUBLIC_NETWORK, \
                        config_util.HYPERVISOR.ESX_API_DEFAULT_PUBLIC_NETWORK)
    host_network = forms.CharField(label="Host Network", initial=network_hint)


class _ChooseNetworkType(_ChooseNetwork):
    network_type = forms.ChoiceField(choices=(("dhcp", "DHCP"),
                                              ("static", "Static"),
                                              ("noip", "No IP configuration")),
                                     initial="noip",
                                     widget=forms.RadioSelect)
    device = forms.ChoiceField(
                       choices=(("eth2", "eth2"),
                                ("eth3", "eth3"),
                                ("eth4", "eth4"),
                                ("eth5", "eth5"),
                                ("eth6", "eth6"),
                                ("eth7", "eth7"),
                                ("eth8", "eth8"),
                                ("eth9", "eth9")))

    def update_choices(self, new_choices, initial=None):
        self.fields["network_type"].choices = new_choices
        if initial:
            self.fields["network_type"].initial = initial

    def set_initial_device(self, device_name):
        self.fields["device"].initial = device_name

    def clean(self):
        if self.is_valid() and hasattr(self, 'validation_callback'):
            form_valid = self.validation_callback(self.cleaned_data)
            # Check whether the callback signalled errors
            if not form_valid[0]:
                raise forms.ValidationError, form_valid[1]
        return self.cleaned_data


class ChooseNetworkWithWorkerShown(ReadOnlyWorker, _ChooseNetwork):
    pass


class ChooseNetworkTypeWithWorkerShown(ReadOnlyWorker, _ChooseNetworkType):
    pass


class PublishService(ChooseWorkerForm, _ChooseNetworkType):
    pass


class DefineStaticNetwork(ReadOnlyWorker):
    ip_address = forms.IPAddressField(label="IP Address")
    netmask = forms.IPAddressField(label="Network Mask")


class ChooseBlockStorage(ChooseWorkerForm):
    storage_type = forms.ChoiceField(
                       choices=(("", "Please select a storage type..."),
                                ("iscsi", "Software iSCSI"),
                                ("xenserver_sm", "XenServer Storage Manager")))


class DefineISCSIDiskSize(ReadOnlyWorker):
    disk_size = forms.IntegerField(label="Disk Size (GB):")


class _RabbitFields(forms.Form):
    hostname = forms.CharField()
    port = forms.IntegerField()
    username = forms.CharField()


class ExternalRabbitMQ(_RabbitFields, PasswordForm):
    pass


class _MySQLFields(forms.Form):
    hostname = forms.CharField()
    username = forms.CharField()


class ExternalMySQL(_MySQLFields, PasswordForm):
    pass


class ScaleOutChooseRole(forms.Form):
    type_of_node = forms.ChoiceField(choices=(("nova-compute",
                                               "Compute Controller"),
                                              ("nova-api", "Compute API")),
                                     widget=forms.RadioSelect)


def generate_choice_entry(node_fqdn, details):
    if details['host_fqdn'] == 'N/A':
        return (node_fqdn, node_fqdn)
    elif details['host_fqdn'].startswith("localhost"):
        return (node_fqdn, "%s (%s)" % (details['host_ipaddress'],
                                        node_fqdn))
    else:
        return (node_fqdn, "%s (%s)" % (details['host_fqdn'],
                                        node_fqdn))
