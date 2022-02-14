#!/usr/bin/env python

import sys
from setuptools import setup

VERSION = '0.0.1'
DESCRIPTION = "Find small moons around planets using shift-and-stack based on JPL Horizons ephemeris"

CLASSIFIERS = list(filter(None, map(str.strip,
"""
Development Status :: 3 - Alpha
Intended Audience :: Science/Research
License :: OSI Approved :: BSD License
Programming Language :: Python
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Programming Language :: Python :: Implementation :: CPython
Topic :: Software Development :: Libraries :: Python Modules
""".splitlines())))

setup(
        name="shift_stack_moons",
        version=VERSION,
        description=DESCRIPTION,
        long_description=DESCRIPTION,
        long_description_content_type="text/x-rst",
        classifiers=CLASSIFIERS,
        author="Ned Molter",
        author_email="emolter@berkeley.edu",
        url="https://github.com/emolter/shift_stack_moons",
        python_requires='>=3',
        license="BSD",
        keywords='planetary astronomy moons jpl ephemeris',
        packages=[],
        platforms=['any'],
        setup_requires=['pytest-runner'],
        tests_require=['pytest']
)