#!/bin/bash
TOOLS=`dirname $0`
VENV=$TOOLS/../.geppetto-venv
source $VENV/bin/activate && $@
