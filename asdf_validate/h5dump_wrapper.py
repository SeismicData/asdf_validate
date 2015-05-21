#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Wrapper around h5dump.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2015
:license:
    BSD 3-Clause ("BSD New" or "BSD Simplified")
"""
import copy
import io
import os
import subprocess
import sys

from lxml import etree


def _etree_to_dict(t, skip_tags):
    d = {t.tag: [_etree_to_dict(_i, skip_tags=skip_tags)
                 for _i in t.iterchildren()]}
    d.update(('@' + k, v) for k, v in t.attrib.iteritems()
             if k not in skip_tags)
    if t.text:
        text = t.text.strip()
        if text:
            d['text'] = text
    return d


def _get_xml_etree_representation(filename):
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
        return etree.parse(fh).getroot()


def _list_of_dicts_to_dict(t, name_key):
    """
    This is a bit complex and ad-hoc but it transforms the output of h5dump to
    something thats easy to validate with jsonschema.
    """
    # Recurse into dictionaries.
    if isinstance(t, dict):
        # If it has a single item "Group", then just use that.
        if list(t.keys()) == ["Group"]:
            return _list_of_dicts_to_dict(t["Group"], name_key)
        for key, value in t.items():
            t[key] = _list_of_dicts_to_dict(value, name_key)
        return t
    # Nothing to do if no list or no dictionaries. We don't consider other
    # containers.
    elif not isinstance(t, list):
        return t
    # Now each item in the list must be a dictionary and must contain the
    # name key
    for item in t:
        if not isinstance(item, dict) or not name_key in item:
            return t

    # Convert list of dictionaries to a simple dictionary. Collect attributes
    # along the way.
    attributes = {}
    ret_val = {}
    for item in t:
        item = copy.copy(item)
        name = item[name_key]
        del item[name_key]

        if "Attribute" in item:
            attributes[name] = _list_of_dicts_to_dict(item["Attribute"],
                                                      name_key)
            continue

        ret_val[name] = _list_of_dicts_to_dict(item, name_key)

    if attributes:
        ret_val["__attributes"] = attributes
    return ret_val


def get_header_as_dict(filename):
    # Skip tags that are not needed for the validation.
    skip_tags = ["OBJ-XID", "H5ParentPaths", "Parents", "H5Path"]

    header = _etree_to_dict(_get_xml_etree_representation(filename),
                            skip_tags=skip_tags)
    # Skip the first level as its just boilerplate.
    header = header["HDF5-File"][0]["RootGroup"]


    # Convert from list of dicts to actual dictionaries.
    header= _list_of_dicts_to_dict(header, name_key="@Name")

    return header
