#!/bin/bash

# Launch this script from your GEPPETTO_HOME
GEPPETTO_HOME=os-vpx-mgmt/geppetto

sync_db()
{
   if [ -f $GEPPETTO_HOME/manage.py ]
   then
       python $GEPPETTO_HOME/manage.py syncdb --noinput
       python $GEPPETTO_HOME/manage.py migrate --verbosity=2
   else
      return 2
   fi
}

sync_db
if [ "$?" -eq 2 ] # manage.py not found
then
  # then try again in local path
  GEPPETTO_HOME=.
  sync_db
fi
