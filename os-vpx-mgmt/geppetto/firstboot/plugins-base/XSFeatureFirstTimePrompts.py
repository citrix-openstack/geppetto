"""First time prompts for the VPX"""

import time
import random
import re
import socket

from XSConsoleStandard import *
from XSConsoleData import *
from threading import Timer
from geppetto.geppettolib.network import ValidateIP

log = logging.getLogger('osconsole')


if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run \
    independently")


default_network_settings = {
    'hostname': 'master',
    'ip': '192.168.1.1',
    'netmask': '255.255.255.0',
    'gateway': '',
    'ntp_server': '192.168.1.1',
    'dns_suffix': 'openstack.com',
    'autosign': 'Yes',
    'first_ip': '192.168.1.100',
    'last_ip': '192.168.1.200',
    'dns_server': '',
    'runinterval': '60',
    'master_name': '',
    'master_ip': '',
}


class NetworkDetailsDialogue(Dialogue):
    """ This asks the user for their network settings.
    It asks a basic set of questions for the master
    and a longer set of questions for the client """
    def __init__(self, in_success_func=None, save_settings_handler=None, \
     show_reduced_fields_for_master=False):
        Dialogue.__init__(self)
        self.on_success_function = in_success_func
        self.save_settings_handler = save_settings_handler
        self.show_reduced_fields_for_master = show_reduced_fields_for_master

        if self.show_reduced_fields_for_master:
            self.text = ("Please specify the network settings for this "
            "machine, DHCP failed to start. Once you have specified the "
            "network settings we will start DHCP, DNS and puppet master "
            "services on the management interface.")
        else:
            self.text = ("Failed to get network details from DHCP, "
            "please specify your network settings:")

        pane = self.NewPane(DialoguePane(self.parent))
        pane.ColoursSet('HELP_BASE', 'HELP_BRIGHT', None, None, None, \
         'HELP_FLASH')
        pane.AddBox()
        pane.TitleSet("Static Network Settings")

        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()

        if self.text is not None:
            pane.AddTitleField(self.text)

        def field(l, k):
            if self.show_reduced_fields_for_master:
                v = default_network_settings[k]
            else:
                v = ''
            pane.AddInputField(Lang(l, 21), v, k)

        field('Hostname', 'hostname')
        field('IP address', 'ip')
        field('Netmask', 'netmask')
        field('Gateway', 'gateway')
        field('NTP Server', 'ntp_server')
        field('DNS Suffix', 'dns_suffix')

        if self.show_reduced_fields_for_master:
            field('Autosign', 'autosign')
            field('First IP', 'first_ip')
            field('Last IP', 'last_ip')
        else:
            field('DNS Server', 'dns_server')
            field('Runinterval', 'runinterval')
            field('Master FQDN', 'master_name')
            field('Master IP', 'master_ip')

        pane.AddKeyHelpField({
            Lang("<Enter>"): Lang("Next/OK"),
            Lang("<Esc>"): Lang("Cancel"),
            Lang("<Tab>"): Lang("Next")
        })

        if pane.InputIndex() is None:
            # Activate first field for input
            pane.InputIndexSet(0)

    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()
                try:
                    # TODO - proper validation
                    if not (self.save_settings_handler == None):
                        self.save_settings_handler(inputValues)
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang('Network settings set Failed: ') + Lang(e)))
                    pane.InputIndexSet(0)
                else:
                    Layout.Inst().PopDialogue()
                    if not (self.on_success_function == None):
                        self.on_success_function(inputValues)
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass
        else:
            handled = False
        return True


class SummaryScreenDialogue(Dialogue):
    """ This displays the current settings of the VPX """
    def __init__(self):
        Dialogue.__init__(self)

        xSize = Layout.Inst().APP_XSIZE - 2
        ySize = Layout.Inst().APP_YSIZE - 2
        paneSizer = PaneSizerFixed(1, 2, xSize, ySize - 1)

        self.text = ("To continue the setup of OpenStack, "
                     "please visit the administration website.")

        pane = self.NewPane(DialoguePane(self.parent, paneSizer))
        pane.ColoursSet('MENU_BASE', 'MENU_BRIGHT', 'MENU_HIGHLIGHT', \
                'MENU_SELECTED')

        self.network_config = \
         DataUtils.Inst().get_all_network_data_for_summary()

        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWrappedBoldTextField(self.text)
        pane.AddWrappedBoldTextField("")

        pane.AddStatusField(Lang('Admin Website', 16),
                        self.network_config.admin_url)
        pane.AddWrappedBoldTextField("")

        pane.AddStatusField(Lang('Hostname', 16),
                            self.network_config.hostname)
        pane.AddStatusField(Lang('IP address', 16),
                            self.network_config.address)
        pane.AddStatusField(Lang('Netmask', 16),
                            self.network_config.netmask)
        if self.network_config.gateway == '0.0.0.0':
            self.network_config.gateway = ''
        pane.AddStatusField(Lang('Gateway', 16),
                            self.network_config.gateway)
        pane.AddStatusField(Lang('DNS Server', 16),
                        self.network_config.dns_server)
        if self.network_config.dns_suffix == 'localhost':
            self.network_config.dns_suffix = ''
        pane.AddStatusField(Lang('DNS Suffix', 16),
                        self.network_config.dns_suffix)
        pane.AddStatusField(Lang('Puppet Master', 16),
                        self.network_config.is_master)

        pane.AddKeyHelpField({Lang("<F5>"): Lang("Refresh"),
                              Lang("<Esc>"): Lang("Quit")})

    def HandleKey(self, inKey):
        handled = True
        if inKey == "KEY_F(5)":
            self.network_config = \
                DataUtils.Inst().get_all_network_data_for_summary()
            self.UpdateFields()
        elif inKey == 'KEY_ESCAPE':
            question = QuestionDialogue("Are you sure you want to quit?",
                            lambda x: (Importer.ActivateNamedPlugIn('Quit') \
                                if (x == 'y') else None))
            Layout.Inst().PushDialogue(question)
        else:
            handled = False
        return handled


class SpecifyMasterHostnameDialogue(Dialogue):
    """
    This is used to ask the user the hostname of the master
    """
    def __init__(self, inHandler):
        Dialogue.__init__(self,)
        self.text = ("Could not automatically find the master. Please "
                    "specify the name of your master.")
        self.handler = inHandler

        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        pane.TitleSet("Specify master")

        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(self.text)
        pane.AddInputField(Lang("Master", 10), "", "master")

        pane.AddKeyHelpField({Lang("<Enter>"): Lang("OK"),
                              Lang("<Esc>"): Lang("Cancel"), })
        pane.InputIndexSet(0)

    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ENTER':
            Layout.Inst().PopDialogue()
            inputValues = self.Pane().GetFieldValues()
            self.handler(inputValues["master"])
        elif inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            self.handler(None)
        elif self.Pane().CurrentInput().HandleKey(inKey):
            pass
        else:
            handled = False

        return handled


class MasterOrClientDialogue(Dialogue):
    """
    This dialogue asks the user if the want this VPX to be
    a puppet master or puppet client.
    While displaying the dialog it polls to see if the
    master can be found
    """
    def __init__(self, handle_master_or_client_answered, handle_found_master,
                dialog_message=None, info_dialog=False):
        self.master_prompt_open = False
        self.no_choice = info_dialog
        self.poll_period = 5
        self.handle_master_or_client_answered = \
                                handle_master_or_client_answered
        self.handle_found_master = handle_found_master
        self.diag_msg = dialog_message

    def show(self):
        self.master_prompt_open = True
        if self.no_choice:
            dialogue = InfoDialogue("Information", self.diag_msg)
        else:
            dialogue = QuestionDialogue("Would you like to become the master?",
                                        self._handle_master_or_client_answered)
        Layout.Inst().PushDialogue(dialogue)
        self._start_polling()

    def _start_polling(self):
        # Let us wait a random amount of seconds,
        # so that we do not overwhelm the master's
        # DHCP/DNS servers during cloud bootstrapping
        random.seed()
        time.sleep(random.uniform(1, 60))
        t = Timer(0.1, self._poll_for_ip)
        t.daemon = True
        t.start()

    def _poll_for_ip(self):
        if self.master_prompt_open:
            if DataUtils.Inst().is_ip_address_configured():
                self._poll_for_master()
            else:
                DataUtils.Inst().restart_network()
                # if no IP is found, restart the network
                # and hope to find one next time
                t = Timer(self.poll_period, self._poll_for_ip)
                t.daemon = True
                t.start()

    def _poll_for_master(self):
        if self.master_prompt_open:
            if DataUtils.Inst().is_master_reachable():
                Layout.Inst().PopDialogue()
                self.handle_found_master()
            else:
                t = Timer(self.poll_period, self._poll_for_master)
                t.daemon = True
                t.start()

    def _handle_master_or_client_answered(self, result):
        self.master_prompt_open = False
        self.handle_master_or_client_answered(result)


class BackgroundWorker():
    @classmethod
    def show_message_while_executing_task(cls, message,
                                        background_task, handle_complete):
        Layout.Inst().PushDialogue(BannerDialogue(message))
        t = Timer(0.1, lambda: cls._start_background_task
                            (background_task, handle_complete))
        t.start()

    @classmethod
    def _start_background_task(cls, background_task, handle_complete):
        try:
            background_task()
        except Exception, e:
            log.error(e)
            Layout.Inst().PopDialogue()
            Layout.Inst().PushDialogue(InfoDialogue("Error", \
                            "Sorry could not complete the requested task"))
        else:
            Layout.Inst().PopDialogue()
            handle_complete()


class XSFeatureFirstTimePrompts:
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'FIRST_TIME_PROMPTS',
            # This key is referred to by name in XSConsoleTerm.py
            {'activatehandler': self.ActivateHandler, })

    PollPeriodInSeconds = 2
    MasterPromptOpen = False

    @classmethod
    def ActivateHandler(cls, *inParams):
        if DataUtils.Inst().is_master() is not None:
            cls.show_summary_screen_dialogue()
        else:
            is_master_in_kernel_cmd = cls._external_config()
            if is_master_in_kernel_cmd is None:
                cls.show_master_or_client_dialogue()
            elif is_master_in_kernel_cmd:
                cls.make_into_master()
            else:
                # We want to turn the VPX into a slave,
                # but we still want to poll for the master
                # to become active.
                msg = ('Boot Options turned this VPX into a slave. '
                      'Polling for the Master...')
                cls.show_master_or_client_dialogue(msg, True)

    @classmethod
    def _external_config(cls):
        cmdline = cls.get_kernel_cmdline()
        if 'geppetto_master=true' in cmdline:
            return True
        elif 'geppetto_master=false' in cmdline:
            return False
        else:
            return None

    @classmethod
    def get_kernel_cmdline(cls):
        return DataUtils.Inst().get_kernel_cmdline()

    @classmethod
    def show_master_or_client_dialogue(cls,
                                       dialog_msg=None,
                                       info_dialog=False):
        master_or_client_dialogue = \
            MasterOrClientDialogue(cls._handle_master_or_client_answered,
                                    cls._handle_found_master,
                                    dialog_msg,
                                    info_dialog)
        master_or_client_dialogue.show()

    @classmethod
    def _handle_master_or_client_answered(cls, answer):
        if answer == 'y':
            cls.make_into_master()
        else:
            cls.make_into_client()

    @classmethod
    def _handle_found_master(cls):
        # TODO - this will want to shortcut the wizard, once added
        cls.make_into_client()

    @classmethod
    def make_into_client(cls):
        BackgroundWorker.\
            show_message_while_executing_task(
                           "Applying configuration for client node...",
                           DataUtils.Inst().make_into_puppet_client,
                           cls.show_summary_screen_dialogue)
        #TODO finish the client wizard -
        #Layout.Inst().PushDialogue(
        #NetworkDetailsDialogue(cls.ShowMasterHostNameSerach))

    @classmethod
    def make_into_master(cls):
        try:
            DataUtils.Inst().set_vpx_is_master_choice(True)
        except Exception, e:
            log.error(e)
            Layout.Inst().PushDialogue(InfoDialogue("Error",
                                        "Sorry had an issue while "
                                        "making this machine a master"))

        if DataUtils.Inst().is_ip_address_configured():
            cls._make_into_master_external_dhcp()
        elif cls._kernel_option_accept_default_networking():
            cls.save_settings_and_start_puppet_and_network_services(
                    default_network_settings)
        elif cls._kernel_option_external_dhcp():
            Layout.Inst().PushDialogue(BannerDialogue("Waiting for \
                            a DHCP server to provide an IP address..."))
            cls._wait_for_ip_then_master_external_dhcp()
        elif DataUtils.Inst()._kernel_option_specify_network_settings():
            network_settings = DataUtils.Inst().\
                            get_ip_settings_from_kernel_args()
            cls.save_settings_and_start_puppet_and_network_services(
                                                            network_settings)
        else:
            cls._make_into_master_internal_dhcp()

    @classmethod
    def _make_into_master_external_dhcp(cls):
        BackgroundWorker.show_message_while_executing_task(
            "Saving network settings...",
            lambda: DataUtils.Inst().configure_master_for_external_dhcp(),
            lambda: cls._start_puppet_master_service())

    @classmethod
    def _make_into_master_internal_dhcp(cls):
        Layout.Inst().PushDialogue(NetworkDetailsDialogue(
                        cls.\
                          save_settings_and_start_puppet_and_network_services,
                          DataUtils.Inst().validate_master_network_settings,
                          True))

    @classmethod
    def _wait_for_ip_then_master_external_dhcp(cls):
        if DataUtils.Inst().is_ip_address_configured():
            Layout.Inst().PopDialogue()
            cls._make_into_master_external_dhcp()
        else:
            DataUtils.Inst().restart_network()
            # if no IP is found, restart the network and
            # hope to find one next time
            t = Timer(10, cls._wait_for_ip_then_master_external_dhcp)
            t.daemon = True
            t.start()

    @classmethod
    def _kernel_option_accept_default_networking(cls):
        return 'geppetto_default_networking=true' in cls.get_kernel_cmdline()

    @classmethod
    def _kernel_option_external_dhcp(cls):
        return 'geppetto_external_dhcp=true' in cls.get_kernel_cmdline()

    @classmethod
    def save_settings_and_start_puppet_and_network_services(cls, values):
        BackgroundWorker.show_message_while_executing_task(
                            "Saving network settings...",
                            lambda: cls._save_master_network_settings(values),
                            lambda: cls._start_network_services(values))

    @classmethod
    def _save_master_network_settings(cls, values):
        ip = ValidateIP.ensure_valid_address(values["ip"], "ip address")
        netmask = ValidateIP.ensure_valid_mask(mask=values["netmask"])
        gateway = ValidateIP.ensure_valid_address(values["gateway"],
                                                  "gateway")
        dns_server = ip
        ntp_server = ValidateIP.ensure_valid_address(
                            values["ntp_server"], "ntp_server")

        hostname = ValidateIP.ensure_valid_hostname(values["hostname"],
                                                    "hostname")
        dns_suffix = ValidateIP.ensure_valid_dns_suffix(
                        values["dns_suffix"], "dns_suffix")

        DataUtils.Inst().set_network_settings(ip, netmask, hostname,
                            dns_server, dns_suffix, gateway, ntp_server)

    @classmethod
    def _start_network_services(cls, values):
        ip = values["ip"]
        netmask = values["netmask"]
        dns_suffix = values["dns_suffix"]
        first_ip = values["first_ip"]
        last_ip = values["last_ip"]
        puppet_master = values["hostname"]

        BackgroundWorker.show_message_while_executing_task(
                            "Starting DNS and DHCP...",
                            lambda: DataUtils.Inst().start_dns_dhcp(ip,
                                                         netmask, dns_suffix,
                                                         first_ip, last_ip,
                                                          puppet_master),
                            cls._start_puppet_master_service)

    @classmethod
    def _start_puppet_master_service(cls):
        BackgroundWorker.show_message_while_executing_task(
                            "Starting puppet master service...",
                            DataUtils.Inst().make_into_puppet_master,
                            cls.show_summary_screen_dialogue)

    @classmethod
    def show_summary_screen_dialogue(cls):
        Layout.Inst().PushDialogue(SummaryScreenDialogue())


# Register this plugin when module is imported
XSFeatureFirstTimePrompts().Register()
