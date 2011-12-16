# Launch this script from your GEPPETTO_HOME
# Make sure that a blank DB file is present in pwd
#
# Supported formats: json, xml, and yaml
#
# Please note that for yaml pyYaml must be installed on your env
#
echo
echo
echo "The script refresh_fixtures.sh has become deprecated after the"
echo "introduction of South (http://south.aeracode.org/docs/index.html)."
echo
echo "South enables schema and data migration. So if you want to make"
echo "schema changes, or add/remove/change data, you have to follow"
echo "South's procedures."
echo
echo "To learn more, please refer to the South's Tutorial available at:"
echo
echo "http://south.aeracode.org/docs/tutorial/index.html."
echo
read -p "Are you sure that you want to proceed? Choose yes only if you know what you are doing (y/n): "

if [ "$REPLY" == "y" -o "$REPLY" == "Y" ]
then
  dir=`dirname "$0"`
  cd $dir/os-vpx-mgmt/geppetto
  FIXTURES=core/fixtures/db_dump.json
  python manage.py geppettodb reset
  python manage.py dumpdata --indent 4 core auth.user --format=json >$FIXTURES
else
  echo "Aborted!"
  exit 1
fi
