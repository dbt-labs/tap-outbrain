#!/usr/bin/env python

from setuptools import setup, find_packages
import os.path

Setup(name='tap-outbrain',
      version='0.0.1',
      description='Streams Outbrain data',
      author='Fishtown Analytics',
      url='https://github.com/stitchstreams/tap-outbrain',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_outbrain'],
      install_requires=[
          'stitchstream-python==0.5.0',
          'backoff==1.3.2',
          'requests==2.13.0'
      ],
      entry_points='''
          [console_scripts]
          tap-outbrain=tap_outbrain:main
      '''
)
