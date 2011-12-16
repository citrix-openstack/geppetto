from django import forms


class UploadImageForm(forms.Form):
    hypervisor_choice = (('xenserver', 'XenServer'), ('esx', 'VMware ESX(i)'))
    oschoice = (('0', 'For VMware ESX(i), Choose OS type'),
                ('ubuntuGuest', 'Ubuntu Linux (32-bit)'),
                ('ubuntu64Guest', 'Ubuntu Linux (64 bit)'),
                ('centosGuest', 'CentOS (32 bit)'),
                ('centos64Guest', 'CentOS (64 bit)'),
                ('dosGuest', 'DOS'))

    label = forms.CharField(max_length=128)
    machine = forms.FileField(label='Machine:')
    kernel = forms.FileField(label='Kernel:', required=False)
    ramdisk = forms.FileField(label='Ramdisk:', required=False)
    js_handler = ("alert('NOTE: Please select OStype if you "
                  "select VMWare ESX(i) as the hypervisor.');")
    attrs_dict = {'onchange': js_handler, }
    hypervisor = forms.ChoiceField(widget=forms.Select(attrs=attrs_dict),
                                   choices=hypervisor_choice,
                                   label='Hypervisor', initial=' ')
    ostype = forms.ChoiceField(choices=oschoice, label='OStype', initial=' ')


class SetupImageContainerForm(forms.Form):
    disk_size = forms.IntegerField(label="Disk Size (GB):")


class ImportPrepForm(forms.Form):
    pass
