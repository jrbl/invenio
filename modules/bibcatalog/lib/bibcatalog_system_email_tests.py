# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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


"""Unit tests for bibcatalog_system_email library."""

import unittest
from invenio.testutils import make_test_suite, run_test_suite
from invenio import bibcatalog_system_email 


class BibCatalogSystemEmailTest(unittest.TestCase):
    """Testing of BibCatalog."""

    def setUp(self):
        self.email = bibcatalog_system_email.BibCatalogSystemEmail()
        bibcatalog_system_email.CFG_BIBCATALOG_SYSTEM_TICKETS_EMAIL = 'eduardo.benavidez@yahoo.com'
        bibcatalog_system_email.CFG_BIBCATALOG_SYSTEM = 'EMAIL'
        pass

    def tearDown(self):
        pass


    def test_email_ticket_search_exception_not_implemented(self):
        """bibcatalog_system_email - execution raises NotImplementedError exception"""

        self.assertRaises(NotImplementedError, self.email.ticket_search, 1)
    
    
    def test_ticket_submit_via_email(self):
        """bibcatalog_system_email - test creating ticket via email"""

        self.assertTrue(self.email.ticket_submit(subject="Issue with RT", text="The RT system is not as good as the email ticketing"))





TEST_SUITE = make_test_suite(BibCatalogSystemEmailTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
