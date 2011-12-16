# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Citrix Systems, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from django.db.utils import IntegrityError
from django.core.validators import ValidationError
from django.core.exceptions import ObjectDoesNotExist


class Failure(Exception):

    def __init__(self, entity, operation, message=None, details=None):
        super(Failure, self).__init__(message)
        self.entity = entity
        self.operation = operation
        self.details = details

    def __str__(self):
        return "for object '%s' on operation '%s'. " \
               "Error message: '%s'." % (self.entity,
                                         self.operation,
                                         super(Failure, self).__str__())

    def get_message(self):
        return super(Failure, self).__str__()


class exception_messages:
    non_unique = 'Element "%s" is non-unique'
    not_found = 'Element "%s" not found'
    not_valid = 'Element "%s" is not valid'


def exception_handler(message=None, entity=None):
    """Exception handler for errors interacting with the model"""
    def decorator_handler(f):
        def f_handler(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
            except (ValidationError, IntegrityError, ObjectDoesNotExist), e:
                entity_tag = entity is None and args[0].__name__ or entity
                entity_val = entity is None and args[1] or args[0]
                raise Failure(entity_tag, f.__name__, message % entity_val, e)
            return result
        return f_handler
    return decorator_handler
