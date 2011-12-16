#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='geppetto',
      version='@VERSION@',
      description='OS-VPX Admin UI by Citrix Systems',
      author='Citrix Systems',
      url='http://citrix.com/',
      packages=find_packages(),
      package_data={
                     'geppetto': ['ui/templates/*.html',
                                  'ui/templates/ui/*.html',
                                  'ui/templates/ui/templatetags/*.html',
                                  'ui/templates/admin/*.html',
                                  'core/templates/*.template',
                                  'core/templates/core/*.yaml',
                                  'core/fixtures/*.json',
                                  ],
                     },
     )
