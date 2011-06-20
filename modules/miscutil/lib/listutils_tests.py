# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Unit tests for listutils library."""

__revision__ = "$Id$"

import unittest

from invenio.listutils import get_mean, get_median, get_mode
from invenio.testutils import make_test_suite, run_test_suite

class MeanTest(unittest.TestCase):
    """Test getting the mean."""

    def test_get_mean_simple(self):
        """listutils - get mean of [1, 2, 3]"""
        self.assertEqual(2, get_mean([1,2,3]))

    def test_get_mean_non_integer(self):
        """listutils - get mean of [1.2, 1.1, 2.3]"""
        self.assertEqual(1.2, get_mean([1.2,1.1,1.3]))

    def test_get_mean_non_number(self):
        """listutils - get mean of ['a', 'b', 'c']"""
        self.assertEqual(0, get_mean(['a','b','c']))

class MedianTest(unittest.TestCase):
    """Test getting the median."""

    def test_get_median_simple(self):
        """listutils - get median of [1, 2, 3]"""
        self.assertEqual(2, get_median([1, 2, 3]))

    def test_median_even_length_list(self):
        """listutils - get median of [2, 1]"""
        self.assertEqual(1, get_median([2, 1]))

    def test_get_median_unsorted(self):
        """listutils - get median of [2, 1, 3]"""
        self.assertEqual(2, get_median([2, 1, 3]))

    def test_get_median_non_number(self):
        """listutils - get median of ['c', 'a', 'b']"""
        self.assertEqual('b', get_median(['c', 'a', 'b']))

class ModeTest(unittest.TestCase):
    """Test getting the mode."""

    def test_get_mode_simple(self):
        """listutils - get mode of [1, 1, 1, 2]"""
        self.assertEqual(1, get_mode([1,1,1,2]))

    def test_get_mode_equal(self):
        """listutils - get mode of [1, 2, 1, 2]"""
        assert get_mode([1,2,1,2]) in [1,2]

    def test_get_mode_non_number(self):
        """listutils - get mode of ['a','b','c']"""
        assert get_mode(['a','b','c']) in ['a', 'b', 'c']

TEST_SUITE = make_test_suite(MeanTest,
                             MedianTest,
                             ModeTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


