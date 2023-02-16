#!/usr/bin/env python
from setuptools import setup

setup(
    name=eessi_tests,
    version=0.0.1,
    description='EESSI test suite',
    url=https://github.com/EESSI/test-suite,
    install_requires=[
    ],
    packages=[eessi.reframe.eessi_utils],
    long_description='This is the test suite used by the EESSI project. '
                     'It contains tests developed for the ReFrame testing framework.'
)
