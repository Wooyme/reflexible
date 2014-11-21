#/usr/bin/env python

from __future__ import print_function

from distutils.dep_util import newer
import os, os.path
from setuptools import setup
import subprocess


# pflexible version
VERSION = open('VERSION').read().strip()
# Create the version.py file
open('pflexible/version.py', 'w').write('__version__ = "%s"\n' % VERSION)

# Build the FortFlex extension if necessary
if (not os.path.exists("pflexible/conv2netcdf4/FortFlex.so") or
    newer("pflexible/conv2netcdf4/fortflex/FortFlex.f",
          "pflexible/conv2netcdf4/FortFlex.so")):
    try:
        print(subprocess.check_output(
            "cd pflexible/conv2netcdf4/fortflex; "
            "sh build_FortFlex.sh", shell=True))
    except:
        print("Problems compiling the FortFlex module.  "
              "Will continue using a slower fallback...")
    else:
        print("FortFlex.so extension has been created in pflexible/conv2netcdf4/!")


def find_package_data(pdir):
    """Recursively get all the data files that are in pdir."""
    return [(d, [os.path.join(d, f) for f in files])
            for d,folders,files in os.walk(pdir)]


setup(
    name = 'pflexible',
    version = VERSION,
    author = 'John F. Burkhart',
    author_email = 'jfburkhart@gmail.com',
    url = 'http://niflheim.nilu.no/~burkhart/pflexible',
    description = 'A Python interface to FLEXPART data.',
    license = 'Creative Commons',
    # ext_modules = [Extension('pflexible.pflexcy', ['pflexible/pflexcy.c'],
    #                          include_dirs=[numpy.get_include()])],
    packages = [
        'pflexible',
        'pflexible.scripts',
        'pflexible.conv2netcdf4',
        'pflexible.tests',
        ],
    data_files = [
        ('pflexible/conv2netcdf4', ['pflexible/conv2netcdf4/FortFlex.so'])] + \
        find_package_data('pflexible/uio_examples'),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'create_ncfile = pflexible.scripts.create_ncfile:main',
        ]
    },

)
