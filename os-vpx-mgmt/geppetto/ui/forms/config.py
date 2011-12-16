from django import forms


class CreateNetwork(forms.Form):
    command_line = forms.CharField(
        initial='--fixed_range_v4=10.0.0.0/24 --label private')


class CreateFloatingIPs(forms.Form):
    command_line = forms.CharField(
        initial='--ip_range=<IP_RANGE>')
