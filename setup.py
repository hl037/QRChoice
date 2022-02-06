#!/usr/bin/env python
import sys

from setuptools import setup, find_packages


def read_file(name):
    """
    Read file content
    """
    f = open(name)
    try:
        return f.read()
    except IOError:
        print("could not read %r" % name)
        f.close()

LONG_DESC = read_file('README.md') + '\n\n' + read_file('HISTORY.md')

EXTRAS = {}

if sys.version_info < (3,):
    EXTRAS['use_2to3'] = True

setup(
    name='QRChoice',
    version='0.1.dev0',
    description='',
    long_description=LONG_DESC,
    long_description_content_type='text/markdown',
    author='Léo Flaventin Hauchecorne',
    author_email='hl037.prog@gmail.com',
    url='https://github.com/hl037/QRChoice',
    license='GPLv3',
    packages=find_packages(),
    test_suite=None,
    include_package_data=True,
    zip_safe=False,
    install_requires=['sqlalchemy>=1.4', 'click>=7', 'rectpack>=0.2.2'],
    extras_require=None,
    entry_points={
      'console_scripts':[
        'qrchoice=qrchoice.cli:main',
      ]
    },
    #package_data={
    #  'module' : ['module/path/to/data', 'path/to/glob/*'],
    #},
    classifiers=[],
    **EXTRAS
)
