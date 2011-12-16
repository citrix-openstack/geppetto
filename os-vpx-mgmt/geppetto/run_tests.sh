#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Geppetto's test suite(s)"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv. Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv. Run tests in local environment"
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  -r, --ignore-puppet      Don't check syntax of Puppet recipes."
  echo "  -p, --ignore-pep8        Don't check for pep8 violations."
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in a virtual environment,"
  echo "      If no virtualenv is found, the script will ask if you would like to create one.  If you "
  echo "      prefer to run tests NOT in a virtual environment, simply pass the -N option."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) let always_venv=1; let never_venv=0;;
    -N|--no-virtual-env) let always_venv=0; let never_venv=1;;
    -f|--force) let force=1;;
    -r|--ignore-puppet) let ignore_puppet=1;;
    -p|--ignore-pep8) let ignore_pep8=1;;
    *) testargs="$testargs $1"
  esac
}

venv=.geppetto-venv
with_venv=tools/with_venv.sh
always_venv=0
never_venv=0
force=0
testargs="--verbosity=2"
wrapper=""
ignore_puppet=0
ignore_pep8=0
syncdb="../../syncdb_from_fixtures.sh"

for arg in "$@"; do
  process_option $arg
done

function run_pep8 {
 [ $ignore_pep8 -eq 1 ] && return 0

  echo -n "Checking for pep8 violations...."
  pep8 $PEP8_INCLUDE $PEP8_OPTIONS
  echo "done!"
}

function run_tests {
  # Just run the test suites in current environment
  ${wrapper} $TESTS
}

function run_puppet_check {
  [ $ignore_puppet -eq 1 ] && return 0

  echo -n "Checking for syntax errors in the Puppet recipes...."
  if [ $(which puppet) ]
  then
    temp_dir=$(mktemp -d)
    mkdir -p $temp_dir/classes/
    cp ../../puppet/recipes/*.pp $temp_dir/classes/
    mv $temp_dir/classes/site.pp $temp_dir/
    puppet --parseonly --verbose $temp_dir/site.pp
    code=$?
    rm -rf $temp_dir
    echo "done!"
    return $code
  else
    echo
    echo "Your dev machine does not have Puppet installed!"
    echo "If you do not want syntax checks of Puppet recipes"
    echo "invoke run_tests.sh with the -r option."
    echo 
    return 1
  fi
}


TESTS="python manage.py test core $testargs"

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ -e ${venv} ]; then
    wrapper="${with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      python tools/install_venv.py
      wrapper="${with_venv}"
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        python tools/install_venv.py
                    wrapper=${with_venv}
      fi
    fi
  fi
fi

# Exclude only deprecated files or files that are auto-generated
PEP8_EXCLUDE=".geppetto-venv*,XSConsoleLang*,atlas_service*,puppet_service*,migrations*"
PEP8_OPTIONS="--exclude=$PEP8_EXCLUDE --repeat --show-pep8 --show-source"
PEP8_INCLUDE="../../os-vpx-mgmt/geppetto \
             ../../os-vpx-scripts/usr/local/bin/geppetto/os-vpx"
run_tests && run_pep8 && run_puppet_check || exit 1
