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

import jsonschema
from lxml import etree

from .h5dump_wrapper import (get_header_as_dict, dump_array_to_file,
                             is_hdf5_file, get_string_attribute)

# Directory of the file.
_DIR = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))

_QUAKEML_SCHEMA = os.path.join(_DIR, "schemas", "QuakeML-1.2.rng")
_STATIONXML_SCHEMA = os.path.join(_DIR, "schemas",
                                  "fdsn-station-1.0.xsd")

# Dictionaries of ASDF schemas by version number.
_ASDF_SCHEMAS = {
    "0.0.2": os.path.join(_DIR, "schemas", "ASDF_0.0.2.json")
}


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

    if not is_hdf5_file(filename):
        _log_error("Not an HDF5 file.")

    file_format = get_string_attribute(filename, "file_format")

    if file_format != "ASDF":
        _log_error("'file_format' attribute in file is '%s' but "
                   "must be 'ASDF'." % file_format)
    file_format_version = get_string_attribute(filename, "file_format_version")
    if file_format_version not in _ASDF_SCHEMAS.keys():
        _log_error("Format version %s not known to validator. "
                   "Known versions:\n\t%s" % (
                    file_format_version, ", ".join(
                        sorted(_ASDF_SCHEMAS.keys()))))

    tempfolder = tempfile.mkdtemp(prefix="tmp_asdf_validate_")
    try:
        if file_format_version == "0.0.2":
            _validate_0_0_2(filename, tmpdir=tempfolder)
        else:
            raise NotImplementedError
    # Always delete the directory!
    finally:
        try:
            shutil.rmtree(tempfolder)
        except:
            pass


def _validate_0_0_2(filename, tmpdir):
    # First validate against the scheme.
    contents = _validate_scheme(filename, scheme_version="0.0.2")

    # Next validate the QuakeML if any.
    if "datasets" in contents and "QuakeML" in contents["datasets"]:
        qml_filename = os.path.join(tmpdir, "quake.xml")
        dump_array_to_file(filename, "/QuakeML", qml_filename)

        # Open schema and file.
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

    # In theory legal but a bit suspicious so warn people.
    if "groups" not in contents:
        _log_warning("Neither waveforms, nor provenance information, nor "
                     "auxiliary data found.")
        return

    # Loop over all waveforms.
    if "Waveforms" in contents["groups"]:
        wf = contents["groups"]["Waveforms"]["groups"]
        for station, items in wf.items():
            items = items["datasets"]

            if "StationXML" not in items:
                continue

            # Dump StationXML to file and validate.
            sxml_filename = os.path.join(tmpdir,
                                         "%s.xml" % station.replace(".", "_"))
            dump_array_to_file(filename, "/Waveforms/%s/StationXML" % station,
                               sxml_filename)

            # Open schema and file.
            schema = etree.XMLSchema(etree.parse(_STATIONXML_SCHEMA))
            xmldoc = etree.parse(sxml_filename)
            valid = schema.validate(xmldoc)

            if not valid:
                msgs = ["Error validating StationXML for %s:" % station]
                for msg in schema.error_log:
                    msgs.append("\t%s" % msg)
                _log_error("\n".join(msgs))
    else:
        # Again warn as a bit funny.
        _log_warning("No waveforms found")


def _validate_scheme(filename, scheme_version):
    header = get_header_as_dict(filename)

    # Open JSON schema.
    with io.open(_ASDF_SCHEMAS[scheme_version], "rt") as fh:
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

    print("Valid ASDF File!")


if __name__ == "__main__":
    main()
