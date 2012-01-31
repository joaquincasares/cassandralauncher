#!/usr/bin/env python

import sys

if sys.version_info < (2, 6):
      sys.stderr.write('Please install (and use) Python2.6, or greater, to run setup.py.\n')
      sys.exit(1)

try:
      from setuptools import setup
except:
      from distutils.core import setup

long_description = """CassandraLauncher contains two parts:

1. `cassandralauncher` is accessible straight from the command line and launches a Cassandra cluster for you.
2. `clusterlauncher` is also accessible from the command line and provides a user interface for AWS and RAX.

Both run off of a config: clusterlauncher.conf.
"""

setup(name='CassandraLauncher',
      version='1.0.1.2',
      description='Command line utilities for launching Cassandra clusters in EC2',
      long_description=long_description,
      author='Joaquin Casares',
      author_email='joaquin.casares AT gmail.com',
      url='http://www.github.com/joaquincasares/cassandralauncher',
      packages=['cassandralauncher'],
      scripts=['scripts/cassandralauncher', 'scripts/clusterlauncher'],
      package_data={'': ['README.md']},
      data_files=[('/etc/cassandralauncher', ['cassandralauncher/clusterlauncher.conf'])],
      keywords="apache cassandra datastax cluster clustertools cloud cloudservers rackspace ec2 aws on-demand",
      install_requires=["boto", "python-cloudservers"]
     )
