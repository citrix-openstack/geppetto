#!/bin/bash
GEPPETTO_PATH=/usr/lib/python2.6/site-packages/geppetto/geppettolib

./rndckeygen.sh
python26 $GEPPETTO_PATH/config_generator.py

config_service()
{
  sudo chkconfig $1 on
  sudo service $1 restart
}

config_service dhcpd
config_service named

