#!/usr/bin/env python
from setuptools import setup, find_packages
import itertools
from langiso639 import __version__

options = dict(
    name='langiso639',
    version=__version__,
    packages=find_packages(),
    license='MIT',
    description='ISO639-3 support for Python.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    package_data={'langiso639': ['languages_utf-8.txt']},
    include_package_data=True,
    author='Jaime Garcia Llopis',
    author_email='jaime.garcia.llopis@gmail.com',
    url='https://github.com/jgarcial/iso639-python',
    install_requires = [],
    extras_require = {}
)

extras = options['extras_require']
extras['full'] = list(set(itertools.chain.from_iterable(extras.values())))
setup(**options)
