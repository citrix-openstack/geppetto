#!/bin/sh

set -eu

thisdir=$(dirname "$0")

cd "$thisdir"

# test_classifier_api.py has a legitimate pep8 violation (expected results)
pep8 -r --exclude=firstboot,views,.geppetto-venv,test_classifier_api.py \
  os-vpx-mgmt

for file in `find os-vpx-scripts puppet -type f -a \! -name .\*~`
do
  if expr "`file $file`" : .*python >/dev/null
  then
    pep8 "$file"
  fi
done
