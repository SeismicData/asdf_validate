#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validator for the ASDF file format indented to be run as a command line
program.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2015
:license:
    BSD 3-Clause ("BSD New" or "BSD Simplified")
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import os
import sys

import h5py

from .h5dump_wrapper import get_header_as_dict


def _log_error(message):
    """
    Print the message to stdout and exit with a non-zero exit code.
    """
    sys.exit(message)


def validate(filename):
    # Start with the very basic checks. Check if the file exists.
    if not os.path.exists(filename):
        _log_error("Path '%s' does not exist." % filename)
    # Make sure its a file.
    if not os.path.isfile(filename):
        _log_error("Path '%s' is not a file." % filename)

    try:
        f = h5py.File(filename, "r")
    except OSError:
        _log_error("Not an HDF5 file.")

    with f:
        _validate(f, filename)


def _validate(f, filename):
    _validate_scheme(filename)


def _validate_scheme(filename):
    header = get_header_as_dict(filename)

    ################
    # DEBUGGING START
    import sys
    __o_std__ = sys.stdout
    sys.stdout = sys.__stdout__
    from IPython.core.debugger import Tracer
    Tracer(colors="Linux")()
    sys.stdout = __o_std__
    # DEBUGGING END
    ################



def main():
    parser = argparse.ArgumentParser(
        description="Validator for ASDF files.")
    parser.add_argument("filename", help="Filename of the ASDF file.")
    args = parser.parse_args()

    filename = args.filename

    validate(filename)


if __name__ == "__main__":
    main()