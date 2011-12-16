import logging
import xmlrpclib

from functools import wraps
from geppetto.core import Failure

logger = logging.getLogger('geppetto.core.views.validators')


class ValidationException(Exception):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return "for '%s' with value: '%s'" % (self.type, self.value)


def xmlrpc_fault_wrapper(f):
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except xmlrpclib.Fault, e:
            raise
        except Failure, e:
            logger.exception(e)
            raise xmlrpclib.Fault(-1, e.get_message())
        except ValidationException, e:
            logger.exception(e)
            raise xmlrpclib.Fault(-2, str(e))
        except Exception, e:
            logger.exception(e)
            raise xmlrpclib.Fault(-3, 'Internal Server Error')
        return result
    return inner


def validate_config(config, config_description):
    """Ensures the config meets the given description. All keys in the input
    config must appear in the config description. All validation functions
    in the config description will be called.

    config: the key/value dictionary of the config
    description: config keys to arrays of validation functions"""
    if config == None:
        config = {}

    for key, _ in config.iteritems():
        if not(key in config_description):
            raise ValidationException("unknown config key", key)

    for key, func_list in config_description.iteritems():
        for func in func_list:
            func(config, key)


def config_required(config, key):
    if not (key in config):
        raise ValidationException("config key required", key)
