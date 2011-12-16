from django import forms
from geppetto.ui.forms.install import generate_choice_entry


class ConfigureLBaaSForm(forms.Form):
    worker = forms.ChoiceField(choices=(("test", "test"), ("test2", "test2")))
    netscaler = forms.IPAddressField(label="NetScaler IP Address",
                                     required=True)
    virtual_ips = forms.CharField(label='Virtual IP Range:', required=True)

    def add_workers_into_form(self, workers):
        node_fqdns = workers.keys()
        node_fqdns.sort()
        choices = [generate_choice_entry(node_fqdn, workers[node_fqdn]) \
                                                  for node_fqdn in node_fqdns]
        self.fields["worker"].choices = \
            [("", "Please select a server...")] + choices


class LoadBalancerAction(forms.Form):
    tenant = forms.ChoiceField(choices=(("test1", "test1"),
                                        ("test2", "test2")))
    operation = forms.ChoiceField(choices=(("list", "List Loadbalancers"),
                                           ("add", "Add Load Balancer"),
                                           ("delete", "Delete Load Balancer")),
                                  initial="flat", widget=forms.RadioSelect)

    def add_tenants_into_form(self, tenants):
        self.fields["tenant"].choices = \
            [(tenant, tenant) for tenant in tenants]


class LoadBalancerSelectVMs(forms.Form):
    friendly_name = forms.CharField()
    port = forms.IntegerField()
    virtual_machines = forms.MultipleChoiceField(choices=(("test", "test"),
                                                          ("test2", "test2")))

    def add_vms_into_form(self, vms):
        self.fields["virtual_machines"].choices = vms

    def clean_virtual_machines(self):
        vms = self.cleaned_data["virtual_machines"]
        if len(vms) < 2:
            raise forms.ValidationError("You must specify at least two VMs.")
        return vms


class LoadBalancerURL(forms.Form):
    url = forms.CharField(label="URL", initial="test",
                          widget=forms.TextInput(
                              attrs={'readonly': 'readonly'}))

    def update_url(self, url):
        self.fields["url"].initial = url


class LoadBalancerList(forms.Form):
    list = forms.CharField(widget=forms.Textarea())

    def update_list(self, list):
        self.fields["list"].initial = list


class LoadBalancerDelete(forms.Form):
    load_balancer = forms.ChoiceField(choices=(("test1", "test1"),
                                               ("test2", "test2")))

    def add_load_balancers_into_form(self, load_balancers):
        self.fields["load_balancer"].choices = load_balancers


class LBaaSInfoForm(forms.Form):
    pass
