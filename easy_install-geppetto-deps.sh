#!/bin/sh

set -ex

MOCK="$1"

# OS-158: install patched version of eventlet-0.9.14 from packages.hg rather than eventlet==0.9.13

# Common dependencies for Openstack Dashboard and Geppetto UI
$MOCK --chroot "easy_install-2.6 -vvv -Z -H None -f /eggs \
                Django==1.3 \
                simplejson==2.1.2
"

# Dependencies for the Geppetto UI
$MOCK --chroot "easy_install-2.6 -vvv -Z -H None -f /eggs \
                celery==2.4.3 \
                django-celery==2.4.2 \
                pyyaml==3.09 \
                south==0.7.3
"

# Dependencies for Geppettolib
$MOCK --chroot "easy_install-2.6 -vvv -Z -H None -f /eggs \
                ipcalc==0.3
"

# Dependencies for the Openstack Dashboard
$MOCK --chroot "easy_install-2.6 -vvv -Z -H None -f /eggs \
                boto==1.9b \
                distribute==0.6.10 \
                django-nose==0.1.2 \
                django-registration==0.7 \
                mox\>=0.5.0 \
                nova-adminclient==0.1.8 \
                nose==1.0.0 \
                django-kombu==0.9.4 \
                django-mailer==0.1.0 \
                importlib==1.0.2 \
                python-cloudfiles==1.7.9.3 \
                python-dateutil==1.5 \
"
