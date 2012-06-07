# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for BibKnowledge."""

import unittest

from invenio import bibknowledge
from invenio.testutils import make_test_suite, run_test_suite, test_web_page_content


class BibknowledgeTests(unittest.TestCase):
    """Unit test functions for bibknowledge."""

    def setUp(self):
        """bibknowledge unit test setup"""
        pass

    def tearDown(self):
        """bbibknowledge unit test cleanup"""
        pass

    def test_get_kbd_values_errors(self):
        """bibknowledge - error conditions in bibknowledge.get_kbd_values"""
        self.assertRaises(ValueError, bibknowledge.get_kbd_values, 'invalidkbname0123987', 'invalidkbsearch0123987')


TEST_SUITE = make_test_suite(BibknowledgeTests)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


