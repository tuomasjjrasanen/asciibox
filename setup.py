# -*- coding: utf-8 -*-
from distutils.core import setup

setup(name='asciibox',
      version='0.4.0',
      description='Render ASCII boxes and arrows as images.',
      author='Tuomas Räsänen',
      author_email='tuomasjjrasanen@tjjr.fi',
      url='http://tjjr.fi/sw/asciibox/',
      packages=['asciibox'],
      package_data={'asciibox': ['data/*'],},
      scripts=['bin/asciibox'],
      license='GPLv3+',
      requires=['docutils'],
      install_requires=['docutils', 'pillow'],
      platforms=['Linux'],
      download_url='http://tjjr.fi/sw/asciibox/releases/asciibox-0.4.0.tar.gz',
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Operating System Kernels :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        ],
      long_description='ASCII Box is a Python program which renders '
      '"boxes and arrows" text diagrams as image files. Currently ASCII Box '
      'can render PNG and SVG files."',
  )
