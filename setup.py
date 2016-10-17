#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) 2013, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from setuptools import setup


__version__ = "0.1.0-dev"


classes = """
    Development Status :: 3 - Alpha
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""


with open('README.rst') as f:
    long_description = f.read()

classifiers = [s.strip() for s in classes.split('\n') if s]

setup(name='qp-shotgun',
      version=__version__,
      long_description=long_description,
      license="BSD",
      description='Qiita Plugin: Shotgun',
      author="Qiita development team",
      author_email="qiita.help@gmail.com",
      url='https://github.com/biocore/qiita',
      test_suite='nose.collector',
      packages=['qp_shotgun', 'qp_shotgun/humann2', 'qp_shotgun/kneaddata', 
                'qp_shotgun/fastqc'],
      package_data={'qp_shotgun': ['support_files/config_file.cfg']},
      scripts=['scripts/configure_shotgun', 'scripts/start_shotgun'],
      extras_require={'test': ["nose >= 0.10.1", "pep8"]},
      install_requires=['click >= 3.3', 'future', 'pandas >= 0.15', 'humann2',
                        'h5py >= 2.3.1', 'biom-format', 'kneaddata >= 0.5.2'],
      dependency_links=[('https://bitbucket.org/biobakery/humann2/get/'
                         '0.9.3.1.tar.gz'),
                        ('https://bitbucket.org/biobakery/kneaddata/get/'
                         '0.5.1.tar.gz#egg=kneaddata-0.5.1')],
      classifiers=classifiers
      )
