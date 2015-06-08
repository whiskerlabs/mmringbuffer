#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
  name = "mmringbuffer",
  version = "0.0.1.dev0",
  description = "A memory-mapped ring buffer implementation in Python.",
  url = "https://github.com/whiskerlabs/mmringbuffer",
  author = "Evan Meagher",
  author_email = "evan@whiskerlabs.com",
  license = "MIT",
  packages = find_packages(),

  # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
  classifiers = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    "Development Status :: 3 - Alpha",

    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python"
  ],

  keywords = "mmap memory mapped ring circular buffer",
)
