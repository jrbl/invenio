# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import unittest
import sys
import re
from invenio.config import CFG_TMPDIR, CFG_ETCDIR

from invenio.authorextract_engine import extract_top_document_information_from_fulltext
from invenio.authorextract_engine import convert_processed_auth_aff_line_to_marc_xml
from invenio.testutils import make_test_suite, run_test_suite


# pylint: disable-msg=C0301

class AuthorextractExtractSectionTest(unittest.TestCase):
    """ authorextract - test finding ref and auth sections """

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize stuff"""
        file = open("%s/authorextract/test1.txt" % CFG_ETCDIR, 'r')
        try:
            self.textbody = [line.decode("utf-8") for line in file.readlines()]
        finally:
            file.close()

    def test_author_finding(self):
        """ find author section """
        (document_info, extract_error, how_start) = extract_top_document_information_from_fulltext(self.textbody)
        authors = document_info['authors']
        print authors
        self.assertEqual(len(authors), 530)


class AuthorextractAuthorParsingTest(unittest.TestCase):
    def setUp(self):
        self.authlines = [
            "B. Aubert,1",
            "M. Bona,1",
            "Y. Karyotakis,1",
            "J. P. Lees,1",
            "V. Poireau,1",
            "E. Prencipe,1",
            "X. Prudent,1",
            "V. Tisserand,1",
            "J. Garra Tico,2",
            "E. Grauges,2""",
            "L. Lopezab    \n",
            "A. Palanoab   \n",
            "M. Pappagalloab    \n",
            "N. L. Blount,56    \n",
            "J. Brau,56     \n",
            "R. Frey,56  ",
            "O. Igonkina,56  ",
            "J. A. Kolb,56  ",
            "M. Lu,56   ",
            "R. Rahmat,56  ",
            "N. B. Sinev,56  ",
            "D. Strom,56   ",
            "J. Strube,56  ",
            "E. Torrence,56   ",
            "G. Castelliab     \n",
            "N. Gagliardiab   \n",
            "M. Margoniab   \n",
            "M. Morandina    \n",
            "M. Posoccoa   \n",
            "M. Rotondoa   \n",
            "F. Simonettoab   \n",
            "R. Stroiliab   \n",
            "C. Vociab   \n",
            "E. Ben",
            "H. Briand,58",
            "G. Calderini,58",
            "J. Chauveau,58",
            "P. David,58",
            "L. Del Buono,58",
            "O. Hamon,58",
            "J. Ocariz,58",
            "A. Perez,58",
            "J. Prendki,58",
            "S. Sitt,58",
            "L. Gladney,59",
            "M. Biasiniab\n",
    ]

    def test_reference_parsing(self):
        """Use a hardcoded set of authors to test the parsing"""
        processed_authors = []
        for l in self.authlines:
            (xml_line, count_auth, count_aff) = \
                convert_processed_auth_aff_line_to_marc_xml(l.replace('\n', ''),
                                                            first_author=False)
            processed_authors.append(xml_line)


TEST_SUITE = make_test_suite(AuthorextractAuthorParsingTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
