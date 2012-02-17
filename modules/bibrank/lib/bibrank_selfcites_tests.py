# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

"""Unit tests for the search engine query parsers."""


import unittest
from datetime import datetime, timedelta

try:
    from mock import patch
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False

from invenio.testutils import make_test_suite, run_test_suite


def get_author_tags_mock():
    return {'collaboration_name': '1'}


def get_fieldvalues_mock(recID, tag):
    return [tag]


def get_personids_from_bibrec_mock(recID):
    graph = {
        1: (1,),
        2: (1, 2),
        3: (2,),
        4: (3,),
        5: (4,),
    }
    return graph[recID]


def get_person_bibrecs_mock(personID):
    graph = {
        1: (1, 2),
        2: (2, 3),
        3: (4,),
        4: (5,),
    }
    return graph[personID]


def get_authors_from_record_mock(recID, tags):
    return get_personids_from_bibrec_mock(recID)


def get_collaborations_from_record_mock(recID):
    return ()


def get_cited_by_mock(*args):
    def f(dummy):
        return args
    return f


def get_record_coauthors(recID):
    coauthors = set()
    for personid in get_personids_from_bibrec_mock(recID):
        recs = get_person_bibrecs_mock(personid)
        for recid in recs:
            coauthors.update(get_personids_from_bibrec_mock(recid))
    return coauthors

# Document Graph
# Docid -> Authorid
# 1 -> 1
# 2 -> 1,2
# 3 -> 2
# 4 -> 3
# 5 -> 4


class SelfCitesIndexerTests(unittest.TestCase):
    """Test utility functions for the summarizer components"""

    def setUp(self):
        from invenio.bibrank_selfcites_task import fill_self_cites_tables
        fill_self_cites_tables()

    def test_get_personids_from_record(self):
        from invenio.bibrank_selfcites_indexer import get_personids_from_record
        self.assert_(get_personids_from_record(1))

    def test_get_person_bibrecs(self):
        from invenio.bibrank_selfcites_indexer import get_person_bibrecs
        get_person_bibrecs(1)

    def test_get_authors_tags(self):
        """
        We don't care about the value since it's
        customizable but verify that it doesn't error
        """
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        tags = get_authors_tags()
        self.assertEqual(len(tags), 4)

    def test_get_authors_from_record(self):
        from invenio.bibrank_selfcites_indexer import get_authors_from_record
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        from invenio.config import CFG_SELFCITES_USE_BIBAUTHORID
        old_config = CFG_SELFCITES_USE_BIBAUTHORID
        tags = get_authors_tags()
        CFG_SELFCITES_USE_BIBAUTHORID = 0
        self.assert_(get_authors_from_record(1, tags))
        CFG_SELFCITES_USE_BIBAUTHORID = 1
        get_authors_from_record(1, tags)
        CFG_SELFCITES_USE_BIBAUTHORID = old_config

    def test_get_collaborations_from_record(self):
        from invenio.bibrank_selfcites_indexer import get_collaborations_from_record
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        tags = get_authors_tags()
        self.assert_(not get_collaborations_from_record(1, tags))

    def test_compute_self_citations(self):
        from invenio.bibrank_selfcites_indexer import compute_self_citations
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        tags = get_authors_tags()
        self.assertEqual(compute_self_citations(1, tags), set())

    def test_fetch_references(self):
        from invenio.bibrank_selfcites_indexer import fetch_references
        self.assertEqual(fetch_references(1), set())

    def test_get_self_cites_list(self):
        from invenio.bibrank_selfcites_indexer import get_self_cites_list
        counts = get_self_cites_list([1,2,3,4])
        self.assertEqual(counts, ((1, 0), (2, 0), (3, 0), (4, 0)))

    def test_get_self_cites(self):
        from invenio.bibrank_selfcites_indexer import get_self_cites
        ret = get_self_cites(1)
        self.assertEqual(ret, 0)

    def test_compute_simple_self_cites(self):
        from invenio.bibrank_selfcites_indexer import compute_simple_self_cites
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        tags = get_authors_tags()
        ret = compute_simple_self_cites([1,2,3,4], tags)
        self.assertEqual(ret, 0)

    def test_get_self_citations_count(self):
        from invenio.bibrank_selfcites_indexer import get_self_citations_count
        ret = get_self_citations_count([1,2,3,4])
        self.assertEqual(ret, 0)

    def test_update_self_cites_tables(self):
        from invenio.bibrank_selfcites_indexer import update_self_cites_tables
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        tags = get_authors_tags()
        update_self_cites_tables(1, tags)

    def test_store_record(self):
        from invenio.bibrank_selfcites_indexer import store_record
        from invenio.bibrank_selfcites_indexer import get_authors_from_record
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        from invenio.dbquery import run_sql
        tags = get_authors_tags()
        recid = 1
        authors = get_authors_from_record(recid, tags)
        sql = 'DELETE FROM rnkRECORDSCACHE WHERE id = %s'
        run_sql(sql, (recid,))
        store_record(recid, authors)
        sql = 'SELECT count(*) FROM rnkRECORDSCACHE WHERE id = %s'
        count = run_sql(sql, (recid,))[0][0]
        self.assert_(count)

    def test_get_author_coauthors_list(self):
        from invenio.bibrank_selfcites_indexer import get_author_coauthors_list
        from invenio.bibrank_selfcites_indexer import get_authors_from_record
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        tags = get_authors_tags()
        authors = get_authors_from_record(1, tags)
        self.assert_(get_author_coauthors_list(authors))

    def test_store_record_coauthors(self):
        from invenio.bibrank_selfcites_indexer import store_record_coauthors
        from invenio.bibrank_selfcites_indexer import get_authors_from_record
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        from invenio.dbquery import run_sql
        tags = get_authors_tags()
        recid = 1
        authors = get_authors_from_record(recid, tags)

        sql = 'DELETE FROM rnkEXTENDEDAUTHORS WHERE id = %s'
        run_sql(sql, (recid,))
        store_record_coauthors(recid, authors)
        sql = 'SELECT count(*) FROM rnkEXTENDEDAUTHORS WHERE id = %s'
        count = run_sql(sql, (recid,))[0][0]
        self.assert_(count)

    def test_get_record_coauthors(self):
        from invenio.bibrank_selfcites_indexer import get_record_coauthors
        self.assert_(get_record_coauthors(1))


class SelfCitesTaskTests(unittest.TestCase):
    def test_check_options(self):
        from invenio.bibrank_selfcites_task import check_options
        self.assert_(not check_options())

    def test_parse_option(self):
        from invenio.bibrank_selfcites_task import parse_option
        parse_option('-a', None, None, None)
        parse_option('-m', None, None, None)
        parse_option('-c', '1', None, None)
        parse_option('-r', '1', None, None)
        parse_option('--recids', '1-10', None, None)
        parse_option('-r', '1,2,3-6', None, None)
        parse_option('--rebuild', None, None, None)

    def test_compute_and_store_self_citations(self):
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        from invenio.bibrank_selfcites_task import compute_and_store_self_citations
        tags = get_authors_tags()
        compute_and_store_self_citations(1, tags)

    def test_rebuild_tables(self):
        from invenio.bibrank_selfcites_task import rebuild_tables
        assert rebuild_tables()

    def test_fetch_bibauthorid_last_update(self):
        from invenio.bibrank_selfcites_task import \
                                                fetch_bibauthorid_last_update
        self.assert_(fetch_bibauthorid_last_update())

    def test_last_updated(self):
        from invenio.bibrank_selfcites_task import fetch_last_updated, \
                                                   store_last_updated
        start_id, start_date, end_date = fetch_last_updated()
        store_last_updated(start_id + 1, start_date)
        new_start_id, new_start_date, new_end_date = fetch_last_updated()
        self.assertEqual(new_start_id, start_id + 1)
        self.assertEqual(new_start_date, start_date)
        self.assertEqual(new_end_date, end_date)
        # Restore value in db
        store_last_updated(start_id, start_date)

    def test_skip_already_processed_records(self):
        from invenio.bibrank_selfcites_task import \
                                            skip_already_processed_records
        arbitrary_date = datetime(year=1, month=1, day=1)
        after_arbitrary_date = arbitrary_date + timedelta(hours=1)
        records = [
            (1, arbitrary_date),
            (2, arbitrary_date),
            (3, arbitrary_date),
            (4, after_arbitrary_date),
        ]
        filtered_records = skip_already_processed_records(records,
                                                          2,
                                                          arbitrary_date)
        self.assertEqual(filtered_records, [
            (3, arbitrary_date),
            (4, after_arbitrary_date),
        ])

    def test_fetch_concerned_records(self):
        from invenio.bibtask import task_set_option
        from invenio.bibrank_selfcites_task import fetch_last_updated, \
                                                   store_last_updated, \
                                                   fetch_concerned_records
        arbitrary_date = datetime(year=1, month=1, day=1)
        # Store values to restore
        start_id, start_date, end_date = fetch_last_updated()
        # Update with our values
        store_last_updated(2, arbitrary_date)
        # Prepare options
        task_set_option('new', True)
        fetch_concerned_records()
        # Restore values
        store_last_updated(start_id, start_date)
        fetch_concerned_records()

    def test_catch_exceptions(self):
        from invenio.bibrank_selfcites_task import catch_exceptions
        def fun():
            return True
        f = catch_exceptions(fun)
        self.assert_(f())

    def test_task_run_core(self):
        from invenio.bibrank_selfcites_task import task_run_core
        task_run_core()

    def test_process_one(self):
        from invenio.bibrank_selfcites_indexer import get_authors_tags
        from invenio.bibrank_selfcites_task import process_one
        tags = get_authors_tags()
        process_one(1, tags)

    def test_empty_self_cites_tables(self):
        from invenio.bibrank_selfcites_task import empty_self_cites_tables
        from invenio.dbquery import run_sql
        empty_self_cites_tables()
        counts = [
            run_sql('SELECT count(*) from rnkRECORDSCACHE')[0][0],
            run_sql('SELECT count(*) from rnkEXTENDEDAUTHORS')[0][0],
            run_sql('SELECT count(*) from rnkSELFCITES')[0][0],
        ]
        self.assertEqual(counts, [0, 0, 0])

    def test_fill_self_cites_tables(self):
        from invenio.bibrank_selfcites_task import fill_self_cites_tables
        from invenio.dbquery import run_sql
        fill_self_cites_tables()
        counts = [
            run_sql('SELECT count(*) from rnkRECORDSCACHE')[0][0],
            run_sql('SELECT count(*) from rnkEXTENDEDAUTHORS')[0][0],
            run_sql('SELECT count(*) from rnkSELFCITES')[0][0],
        ]
        self.assert_(counts[0] > 0)
        self.assert_(counts[1] > 0)
        self.assert_(counts[2] > 0)


class SelfCitesOtherTests(unittest.TestCase):
    if HAS_MOCK:
        @patch('invenio.bibrank_selfcites_indexer.get_fieldvalues',
            get_fieldvalues_mock)
        def get_collaborations_from_record(self):
            """
            Check that it's fetching collaborations
            """
            from invenio.bibrank_selfcites_indexer import get_collaborations_from_record

            tags = get_author_tags_mock()
            collaborations = get_collaborations_from_record(2, tags)
            self.assertEqual(collaborations, ['1'])

        @patch('invenio.bibrank_selfcites_indexer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.bibrank_selfcites_indexer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.bibrank_selfcites_indexer.get_cited_by',
            get_cited_by_mock(4, 5))
        @patch('invenio.bibrank_selfcites_indexer.get_record_coauthors',
            get_record_coauthors)
        def test_compute_self_citations_no_self_citations(self):
            """
            Check self citations count matches when no self citations
            are present

            see document graph up in this file
            """
            from invenio.bibrank_selfcites_indexer import compute_self_citations
            tags = get_author_tags_mock()
            self_citations = compute_self_citations(1, tags)
            self.assertEqual(self_citations, set())

        @patch('invenio.bibrank_selfcites_indexer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.bibrank_selfcites_indexer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.bibrank_selfcites_indexer.get_cited_by',
            get_cited_by_mock(3, 4))
        @patch('invenio.bibrank_selfcites_indexer.get_record_coauthors',
            get_record_coauthors)
        def test_compute_self_citations(self):
            """Check self citations count matches in a typical case

            1 has a self-citation
            see document graph up in this file
            """
            from invenio.bibrank_selfcites_indexer import compute_self_citations
            tags = get_author_tags_mock()
            self_citations = compute_self_citations(1, tags)
            self.assertEqual(self_citations, set([3]))

        @patch('invenio.bibrank_selfcites_indexer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.bibrank_selfcites_indexer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.bibrank_selfcites_indexer.get_cited_by',
            get_cited_by_mock(1, 2, 3))
        @patch('invenio.bibrank_selfcites_indexer.get_record_coauthors',
            get_record_coauthors)
        def test_compute_self_citations_all_self_citations(self):
            """
            Check self citations count matches when all citations
            are self citations

            see document graph up in this file
            """
            from invenio.bibrank_selfcites_indexer import compute_self_citations
            tags = get_author_tags_mock()
            total_citations = compute_self_citations(1, tags)
            self.assertEqual(total_citations, set([1,2,3]))


TEST_SUITE = make_test_suite(SelfCitesIndexerTests,
                             SelfCitesTaskTests,
                             SelfCitesOtherTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
