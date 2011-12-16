import string

from django.test import TestCase

from geppetto.core.models import ConfigClass
from geppetto.core.models import ConfigClassParameter

import logging
logger = logging.getLogger('geppetto.core.tests.puppet_recipes')

CONFIG_PP = '../../puppet/recipes/config.pp'
DEPS_PP = '../../puppet/recipes/deps.pp'

IGNORE_PARAMS = ['MYSQL_TYPE', ]
IGNORE_CLASSES = ['openstack-role-set', ]


class TestPuppetRecipes(TestCase):
    def setUp(self):
        super(TestPuppetRecipes, self).setUp()
        self.configs = _read_puppet_pps(CONFIG_PP)
        self.deps = _read_puppet_pps(DEPS_PP)

    def tearDown(self):
        super(TestPuppetRecipes, self).tearDown()

    def testConfigParamsConsistency(self):
        for config in ConfigClass.objects.all():
            recipe_snippet = _get_class_str(self.configs, config.name)
            if recipe_snippet:
                # This is a config class, we need to check
                # that all params are present
                params = ConfigClassParameter.\
                    objects.\
                    filter(config_class=config)
                for param in params:
                    l_value = param.name
                    r_value = '$%s' % l_value
                    l_value_found = string.find(recipe_snippet, l_value)
                    r_value_found = string.find(recipe_snippet,
                                                r_value,
                                                l_value_found)
                    if  (l_value_found == -1 or r_value_found == -1) and \
                         l_value not in IGNORE_PARAMS:
                        raise Exception('%(param)s error in %(recipe_snippet)s'
                                        % locals())
                    else:
                        logger.debug('%(param)s found in %(config)s class.' %
                                  locals())
            else:
                recipe_snippet = _get_class_str(self.deps, config.name)
                if recipe_snippet:
                    # This is a dep class, we need to check
                    # that we touch the correct file
                    pass
                elif config.name not in IGNORE_CLASSES:
                    raise Exception(
                            'Class %s not found in any recipes. Please check!'
                            % config.name)
        logger.debug('All good, you can go!')


def _get_class_str(classes, class_name):
    str_match = '%s {' % class_name
    start = string.find(classes, str_match)
    end = string.find(classes,
                      'class',
                      start)
    if end > start and start > -1:
        # that's a class in the middle of the file
        return classes[start:end - 1]
    elif end == -1 and start > -1:
        # that's a class at the end of the file
        return classes[start:]
    else:
        # no luck
        return None


def _read_puppet_pps(filename):
    with open(filename) as f:
        return f.read()
