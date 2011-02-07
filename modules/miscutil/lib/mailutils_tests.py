# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011 CERN.
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

"""Unit tests for the email utils."""


import unittest

from invenio.mailutils import well_formed

from invenio.testutils import make_test_suite, run_test_suite

class TestMailUtilityFunctions(unittest.TestCase):
    """Test utility functions for the mail components"""

    def test_wf_empty(self):
        """well_formed: ''"""
        self.assertEqual(False, well_formed(''))

    def test_wf_none(self):
        """well_formed: None"""
        self.assertEqual(False, well_formed(None))

    def test_wf_plain(self):
        """well_formed: cal@iamcalx.com"""
        self.assertEqual(True, well_formed('cal@iamcalx.com'))

    def test_wf_site_extension(self):
        """well_formed: cal+henderson@iamcalx.com"""
        self.assertEqual(True, well_formed('cal+henderson@iamcalx.com'))

    def test_wf_extra_word(self):
        """well_formed: 'cal henderson@iamcalx.com'"""
        self.assertEqual(False, well_formed('cal henderson@iamcalx.com'))

    def test_wf_extra_quotes(self):
        """well_formed: '"cal henderson"@iamcalx.com'"""
        self.assertEqual(True, well_formed('"cal henderson"@iamcalx.com'))

    def test_wf_missing_tld(self):
        """well_formed: 'cal@iamcalx'"""
        self.assertEqual(True, well_formed('cal@iamcalx'))

    def test_wf_extra_word_missing_tld(self):
        """well_formed: 'cal@iamcalx com'"""
        self.assertEqual(False, well_formed('cal@iamcalx com'))

    def test_wf_broken_domain_name(self):
        """well_formed: 'cal@hello world.com'"""
        self.assertEqual(False, well_formed('cal@hello world.com'))

    def test_wf_bracketed_domain(self):
        """well_formed: 'cal@[hello world].com'"""
        self.assertEqual(True, well_formed('cal@[hello world].com'))

    def test_wf_very_long_missing_tld(self):
        """well_formed: 'abcdefghijklmnopqrstuvwxyz@abcdefghijklmnopqrstuvwxyz'"""
        self.assertEqual(True, well_formed('abcdefghijklmnopqrstuvwxyz@abcdefghijklmnopqrstuvwxyz'))


TEST_SUITE = make_test_suite(TestMailUtilityFunctions)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
