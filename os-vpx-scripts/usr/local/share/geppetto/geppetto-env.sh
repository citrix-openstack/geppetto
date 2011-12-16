#!/bin/bash

export PYTHON_EGG_CACHE=/tmp/$(whoami)/PYTHON_EGG_CACHE

export GEPPETTO_BIN_PATH=/usr/local/bin/geppetto
export GEPPETTO_SHARE_PATH=/usr/local/share/geppetto
export GEPPETTO_LIB_PATH=/var/lib/geppetto

export PATH=$GEPPETTO_BIN_PATH:$GEPPETTO_BIN_PATH/os-vpx:$PATH

. $GEPPETTO_SHARE_PATH/networking.sh
