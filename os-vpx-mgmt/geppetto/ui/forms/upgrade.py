import logging

from django import forms
from geppetto.ui.forms.install import generate_choice_entry

logger = logging.getLogger('geppetto.ui.views')


class SelectWizardForm(forms.Form):
    openstack_worker = forms.ChoiceField()

    def load_worker_roles(self, compositions):
        items = compositions.items()
        items.sort()
        choices = [(roles, d) for d, roles in items]
        self.fields['openstack_worker'].choices = \
                        [('', 'Please select a worker type...')] + choices

    def get_openstack_worker_label(self, worker):
        for roles, d in self.fields['openstack_worker'].choices:
            if str(roles) == str(worker):
                return d


class MigrationWizardForm(forms.Form):
    old_vpx = forms.ChoiceField()
    new_vpx = forms.ChoiceField()

    def load_nodes(self, o_vpxs, n_vpxs):
        self._load_nodes('old_vpx', o_vpxs)
        self._load_nodes('new_vpx', n_vpxs)

    def _load_nodes(self, label, vpxs):
        node_fqdns = vpxs.keys()
        node_fqdns.sort()
        choices = [generate_choice_entry(node_fqdn, vpxs[node_fqdn]) \
                                                for node_fqdn in node_fqdns]
        self.fields[label].choices = \
                        [('', 'Please select a vpx...')] + choices


class WarningWizardForm(forms.Form):
    pass
