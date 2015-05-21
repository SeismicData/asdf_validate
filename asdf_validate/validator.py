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
import inspect
import io
import json
import os
import sys

import h5py
import jsonschema

from .h5dump_wrapper import get_header_as_dict

# Directory of the file.
_DIR = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))


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

    # Open JSON schema.
    with io.open(os.path.join(_DIR, "asdf_schema.json"), "rt") as fh:
        schema = json.load(fh)

    # Validate the schema to avoid silly errors.
    jsonschema.Draft4Validator.check_schema(schema)

    # Validate h5dump output against schema.
    jsonschema.validate(header, schema)


def main():
    parser = argparse.ArgumentParser(
        description="Validator for ASDF files.")
    parser.add_argument("filename", help="Filename of the ASDF file.")
    args = parser.parse_args()

    filename = args.filename

    validate(filename)


if __name__ == "__main__":
    main()
