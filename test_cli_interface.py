#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the ASDF validator script.

Most of these will actually execute via subprocess calls to test how people
will actually use it.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2015
:license:
    BSD 3-Clause ("BSD New" or "BSD Simplified")
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import os
import subprocess

import pytest


@pytest.fixture
def cli(request):
    """
    Fixture for being able to easily test command line output.

    Usage:
        output = cli.run("ls")
    """
    Output = collections.namedtuple(
            "Output", ["stdout", "stderr", "exit_status", "cmd"])

    def run(command):
        args = command.split()

        p = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        stdout = stdout.decode()
        stderr = stderr.decode()

        return Output(stdout=stdout, stderr=stderr,
                      exit_status=p.returncode, cmd=command)

    request.run = run
    return request


def test_non_existing_file(tmpdir, cli):
    """
    Tests the error message for a non-existing file.
    """
    output = cli.run("asdf-validate %s" % os.path.join(tmpdir.dirname,
                                                       "random"))
    assert output.exit_status == 1
    assert output.stdout == ""
    assert "does not exist" in output.stderr.lower()


def test_error_message_not_a_file(tmpdir, cli):
    """
    Tests the error message if the given path is not a file.
    """
    output = cli.run("asdf-validate %s" % tmpdir.dirname)

    assert output.exit_status == 1
    assert output.stdout == ""
    assert "is not a file" in output.stderr.lower()
