import logging

from geppetto.tests.test_geppetto_api import TestGeppettoServiceAPI
from geppetto.tests.test_classifier_api import TestClassifierServiceAPI
from geppetto.tests.test_puppet_services import TestPuppetServices
from geppetto.tests.test_puppet_recipes import TestPuppetRecipes
from geppetto.tests.test_geppetto_model import TestGeppettoModel
from geppetto.tests.test_hapi_layer import TestHAPI
from geppetto.tests.test_geppettolib import TestGeppettoLib, TestValidateIP
from geppetto.tests.test_xsconsoledata import TestXSConsoleData


logger = logging.getLogger()
fhdlr = logging.FileHandler('run_tests.log', 'w')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fhdlr.setFormatter(formatter)
logger.handlers = []
logger.addHandler(fhdlr)
logger.setLevel(logging.DEBUG)

logger.debug('Testing: %s ' % TestGeppettoServiceAPI)
logger.debug('Testing: %s ' % TestClassifierServiceAPI)
logger.debug('Testing: %s ' % TestPuppetRecipes)
logger.debug('Testing: %s ' % TestPuppetServices)
logger.debug('Testing: %s ' % TestGeppettoModel)
logger.debug('Testing: %s ' % TestHAPI)
logger.debug('Testing: %s ' % TestGeppettoLib)
logger.debug('Testing: %s ' % TestValidateIP)
logger.debug('Testing: %s ' % TestXSConsoleData)
