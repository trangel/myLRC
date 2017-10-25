from __future__ import print_function
import os
import shutil

from setuptools import find_packages #, setup
from distutils.core import setup


#---------------------------------------------------------------------------
# Basic project information
#---------------------------------------------------------------------------

__version__ = '1.4.0'

name = 'myLRC'
description = """
My personnal module to create jobs on LRC servers.
"""
author = 'Tonatiuh Rangel'


#---------------------------------------------------------------------------
# Helper functions
#---------------------------------------------------------------------------

def cleanup():
    """Clean up the junk left around by the build process."""

    egg = 'myLRC.egg-info'
    try:
        shutil.rmtree(egg)
    except Exception as E:
        print(E)
        try:
            os.unlink(egg)
        except:
            pass

#---------------------------------------------------------------------------
# Setup
#---------------------------------------------------------------------------


setup_args = dict(
      name             = name,
      version          = __version__,
      description      = description,
      author           = author,
      license          = license,
      packages         = find_packages(),
      )

if __name__ == "__main__":
    setup(**setup_args)
    cleanup()

