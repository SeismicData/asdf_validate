#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to get a nice dictionary/JSON representation of the data structure of
any HDF5 file.

The goal is to get the structure in a fairly simple form thus that JSONSchema
can be used to validate it.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2015
:license:
    BSD 3-Clause ("BSD New" or "BSD Simplified")
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import io
import os
import re
import subprocess
import sys

import xmltodict


def _get_header_dict_representation(filename):
    if not os.path.exists(filename):
        sys.exit("File '%s' does not exist." % filename)
    args = ["h5dump", "-H", "-u", filename]
    p = subprocess.Popen(args, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stderr = stderr.decode()

    if stderr:
        sys.exit("stderr when running h5dump: %s" % stderr)
    if p.returncode != 0:
        sys.exit("Returncode when running h5dump: %i" % p.returncode)

    with io.BytesIO(stdout) as fh:
        return xmltodict.parse(fh)


def dump_array_to_file(hdf5_file, dataset_name, output_file):
    """
    Gets a specified dataset from an HDF5 file and dumps it to output_file.
    """
    output_file = os.path.abspath(output_file)
    if not os.path.exists(hdf5_file):
        sys.exit("File '%s' does not exist." % hdf5_file)
    if not os.path.exists(os.path.dirname(output_file)):
        sys.exit("Folder '%s' does not exist." % os.path.dirname(output_file))
    args = ['h5dump', '-d', dataset_name, '-b', '-o', output_file,
            hdf5_file]
    subprocess.check_output(args)


def is_hdf5_file(filename):
    """
    Determine if the file is an HDF5 file using h5ls. If it fails its no HDF5
    file.
    """
    if not os.path.exists(filename):
        sys.exit("File '%s' does not exist." % filename)
    args = ["h5ls", filename]
    try:
        subprocess.check_output(args, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False


def _get_attribute(filename, path):
    if not os.path.exists(filename):
        sys.exit("File '%s' does not exist." % filename)
    args = ["h5dump", "-e", "-a", path, filename]
    p = subprocess.Popen(args, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()

    if "unable to open attribute" in stderr.lower():
        sys.exit("Could not find attribute '%s' in file." % path)

    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("(0):"):
            continue
        line = line[len("(0):"):].strip()
        return line

    raise ValueError("Problem decoding attribute '%s' in file." % path)


def get_string_attribute(filename, path):
    attrib = _get_attribute(filename, path)
    if not attrib.startswith('"') or not attrib.endswith('"'):
        raise ValueError("Problem decoding attribute '%s' in file." % path)
    attrib = attrib[1:-1]
    # Zero padded terminated and potentially padded string.
    attrib = re.sub(r"\\0+$", "", attrib)
    return attrib


def get_float_attribute(filename, path):
    attrib = _get_attribute(filename, path)
    return float(attrib)


def r_remove_keys(d, keys):
    """
    Recursively remove all keys from all dictionaries in d. Will recurse into
    any list and dictionary like object.
    """
    if isinstance(d, list):
        return [r_remove_keys(_i, keys) for _i in d]
    # Any dictionary like object.
    elif isinstance(d, collections.Mapping):
        # Remove all unwanted keys. This also stop recursion for the
        # child elements.
        for key in keys:
            try:
                del d[key]
            except KeyError:
                pass
        for key, item in d.items():
            d[key] = r_remove_keys(item, keys)
        return d
    else:
        return d


def r_transform_dict(d):
    """
    Recursively transforms the dictionary by hard-coded rules with the goal of
    making it more readable and ultimately provide better error messages.
    """
    if isinstance(d, list):
        return [r_transform_dict(_i) for _i in d]
    # Any dictionary like object.
    elif isinstance(d, collections.Mapping):
        # All transformations happens in here.

        # All datatypes in ASDF are atomic. We can force this here and flatten
        # the structure a bit.
        if "DataType" in d:
            dt = d["DataType"]
            # Custom extensions might have compound types so we leave them in.
            # If a composite type is used in an ASDF defined structure the
            # scheme will raise an error.
            if list(dt.keys()) == ["AtomicType"]:
                d["DataType"] = dt["AtomicType"]

        # Rename certain keys to make it easier to read.
        renames = {"Attribute": "attributes",
                   "Group": "groups",
                   "Dataset": "datasets"}
        for src, dst in renames.items():
            if src in d:
                data = d[src]
                del d[src]
                d[dst] = data

        def _to_bool(value):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            else:
                raise ValueError

        # Force the types of certain keys if possible.
        conversions = {
            "@StrSize": int,
            "@Size": int,
            "@DimSize": int,
            "@MaxDimSize": int,
            "@Ndims": int,
            "@Sign": _to_bool,
            "@SignBitLocation": int,
            "@ExponentBits": int,
            "@ExponentLocation": int,
            "@MantissaBits": int,
            "@MantissaLocation": int}
        for key, convert in conversions.items():
            if key in d:
                data = d[key]
                del d[key]
                try:
                    d[key] = convert(data)
                except ValueError:
                    d[key] = data

        # Now check if any of the value is a list of dictionaries and each
        # dictionary has a "@Name" key. In that case it can be rewritten as a
        # dict.
        # Alternatively the value can be a dictionary with a '@Name' key.
        for key, value in d.items():
            # A single item will just be written as a dictioary by xmltodict.
            if isinstance(value, collections.Mapping) and "@Name" in value:
                name = value["@Name"]
                del value["@Name"]
                d[key] = {name: value}
            if not isinstance(value, list):
                continue

            if not all(isinstance(_i, collections.Mapping) for _i in value):
                continue

            if not all("@Name" in _i for _i in value):
                continue

            new_value = {}
            for item in value:
                name = item["@Name"]
                del item["@Name"]
                new_value[name] = item
            d[key] = new_value

        for key, value in d.items():
            d[key] = r_transform_dict(value)
        return d
    else:
        return d


def get_header_as_dict(filename):
    """
    Get a nice representation of the HDF5 datastructure as a dictionary.
    """
    header = \
        _get_header_dict_representation(filename)["HDF5-File"]["RootGroup"]

    # List of keys that are just noise and will be removed.
    ignore_keys = [
        # The internal HDF5 id.
        "@OBJ-XID",
        "@H5ParentPaths",
        "@Parents",
        "@H5Path",
        # HDF5 internal value that really does not concern ASDF.
        "FillValueInfo",
        # We only get the header information from h5dump. Thus there never is
        # any data. A group named `Data` in an HDF5 file would furthermore be
        # stored in the "@Name" field thus this is save to do.
        "Data",
        # The storage layout does also not matter for the ASDF definition. Is
        # is important for any single application but does not matter for the
        # ASDF format itsself.
        "StorageLayout"
        ]

    # Recursively remove all the unwanted keys.
    header = r_remove_keys(header, ignore_keys)

    # Transfrom the dictionary to make it easier to read.
    header = r_transform_dict(header)

    with open("./dummy.json", "w") as fh:
        import json
        json.dump(header, fh, indent=4)

    return header
