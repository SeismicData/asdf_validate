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
import shutil
import sys
import tempfile

import h5py
import jsonschema
from lxml import etree

from .h5dump_wrapper import get_header_as_dict, dump_array_to_file

# Directory of the file.
_DIR = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))

_QUAKEML_SCHEMA = os.path.join(_DIR, "schemas", "QuakeML-1.2.rng")


def _log_error(message):
    """
    Print the message to stdout and exit with a non-zero exit code.
    """
    sys.exit(message)


def _log_warning(message):
    """
    Print the message to stdout
    """
    print(message)


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

    tempfolder = tempfile.mkdtemp(prefix="tmp_asdf_validate_")
    try:
        with f:
            _validate(f, filename, tmpdir=tempfolder)
    # Always delete the directory!
    finally:
        try:
            shutil.rmtree(tempfolder)
        except:
            pass


def _validate(f, filename, tmpdir):
    # First validate against the scheme.
    contents = _validate_scheme(filename)

    # Next validate the QuakeML if any.
    if "datasets" in contents and "QuakeML" in contents["datasets"]:
        qml_filename = os.path.join(tmpdir, "quake.xml")
        dump_array_to_file(filename, "/QuakeML", qml_filename)

        # Open schema and file..
        relaxng = etree.RelaxNG(etree.parse(_QUAKEML_SCHEMA))
        xmldoc = etree.parse(qml_filename)
        valid = relaxng.validate(xmldoc)

        if not valid:
            msgs = ["Error validating QuakeMl:"]
            for msg in relaxng.error_log:
                msgs.append("\t%s" % msg)
            _log_error("\n".join(msgs))
    else:
        _log_warning("No QuakeML found in the file.")


def _validate_scheme(filename):
    header = get_header_as_dict(filename)

    # Open JSON schema.
    with io.open(os.path.join(_DIR, "asdf_schema.json"), "rt") as fh:
        schema = json.load(fh)

    # Validate the schema itself to avoid silly errors.
    jsonschema.Draft4Validator.check_schema(schema)

    # Validate the h5dump output against the schema.
    jsonschema.validate(header, schema)
    return header


def main():
    parser = argparse.ArgumentParser(
        description="Validator for ASDF files.")
    parser.add_argument("filename", help="Filename of the ASDF file.")
    args = parser.parse_args()

    filename = args.filename

    validate(filename)


if __name__ == "__main__":
    main()
