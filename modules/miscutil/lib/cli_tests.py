#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########+#########+#########+#########+#########+#########+#########+#########
# Copyright (C) 2010  SLAC National Accelerator Laboratory
#
#This program is free software: you can redistribute it and/or modify it under
#the terms of the GNU General Public License as published by the Free Software
#Foundation, either version 3 of the License, or (at your option) any later
#version.
#
#This program is distributed in the hope that it will be useful, but WITHOUT
#ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#details.
#
#You should have received a copy of the GNU General Public License along with
#this program.  If not, see <http://www.gnu.org/licenses/>.
"""Unit tests for the Invenio command-line module"""

import unittest

from invenio import cli

from invenio.testutils import make_test_suite, run_test_suite


class TestCLI(unittest.TestCase):
    """Test CLI"""

    def setUp(self):
        """Create initial conditions for CLI unit testing"""
        pass

    def test_get_cite_counts(self):
        """Test CLI: cite counts for an arbitrary query"""
        self.assertEqual([x for x in cli.get_cite_counts('recid:81')],
                         [(81, 4)])

    def test_irn(self):
        """Test CLI: IRN lookup by recid"""
        self.assertEqual(cli.irn(95),
                         '000289446CER')


CLI_TESTS = make_test_suite(TestCLI)


if __name__ == "__main__":
    run_test_suite(CLI_TESTS)

