# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""
Self citations task

Stores self-citations in a table for quick access
"""

import sys
import traceback
from datetime import datetime

from invenio.config import CFG_VERSION, CFG_SELFCITES_USE_BIBAUTHORID
from invenio.bibtask import task_init, task_set_option, \
                            task_get_option, write_message, \
                            task_sleep_now_if_required, \
                            task_update_progress
from invenio.dbquery import run_sql
from invenio.docextract_task import task_run_core_wrapper, split_ids
from invenio.bibrank_selfcites_indexer import update_self_cites_tables, \
                                              compute_self_citations, \
                                              get_authors_tags
from invenio.bibrank_citation_searcher import get_refers_to
from invenio.bibauthorid_daemon import get_user_log as bibauthorid_user_log
from invenio.bibrank_citation_indexer import get_bibrankmethod_lastupdate

HELP_MESSAGE = """
  Scheduled (daemon) self cites options:
  -a, --new          Run on all newly inserted records.
  -m, --modified     Run on all newly modified records.
  -r, --recids       Record id for extraction.
  -c, --collections  Entire Collection for extraction.
  --rebuild          Rebuild pre-computed tables
                     * nnkRECORDSCACHE
                     * rnkEXTENDERAUTHORS
                     * rnkSELFCITES

  Examples:
   (run a daemon job)
      selfcites -a
   (run on a set of records)
      selfcites --recids 1,2 -r 3
   (run on a collection)
      selfcites --collections "Reports"

"""
"Shown when passed options are invalid or -h is specified in the CLI"

DESCRIPTION = """This task handles the self-citations computation
It is run on modified records so that it can update the tables used for
displaying info in the citesummary format
"""
"Description of the task"

NAME = 'selfcites'


def check_options():
    """Check command line options"""
    if not task_get_option('new') \
            and not task_get_option('modified') \
            and not task_get_option('recids') \
            and not task_get_option('collections') \
            and not task_get_option('rebuild'):
        print >>sys.stderr, 'Error: No input file specified, you need' \
            ' to specify which files to run on'
        return False

    return True


def parse_option(key, value, dummy, args):
    """Parse command line options"""

    if args:
        # There should be no standalone arguments for any refextract job
        # This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-a', '--new'):
        task_set_option('new', True)
    elif key in ('-m', '--modified'):
        task_set_option('modified', True)
    elif key == '--rebuild':
        task_set_option('rebuild', True)
    elif key in ('-c', '--collections'):
        collections = task_get_option('collections')
        if not collections:
            collections = set()
            task_set_option('collections', collections)
        collections.update(split_ids(value))
    elif key in ('-r', '--recids'):
        recids = task_get_option('recids')
        if not recids:
            recids = set()
            task_set_option('recids', recids)
        recids.update(split_ids(value))

    return True


def compute_and_store_self_citations(recid, tags, verbose=False):
    """Compute and store self-cites in a table

    Args:
     - recid
     - tags: used when bibauthorid is desactivated see get_author_tags()
            in bibrank_selfcites_indexer
    """
    assert recid

    if verbose:
        write_message("* processing %s" % recid)
    references = get_refers_to(recid)
    recids_to_check = set([recid]) | set(references)
    placeholders = ','.join('%s' for r in recids_to_check)
    rec_row = run_sql("SELECT MAX(`modification_date`) FROM `bibrec`"
                      " WHERE `id` IN (%s)" % placeholders, recids_to_check)

    try:
        rec_timestamp = rec_row[0]
    except IndexError:
        write_message("record not found")
        return

    cached_citations_row = run_sql("SELECT `count` FROM `rnkSELFCITES`"
               " WHERE `last_updated` >= %s" \
               " AND `id` = %s", (rec_timestamp[0], recid))
    if cached_citations_row and cached_citations_row[0][0]:
        if verbose:
            write_message("%s found (cached)" % cached_citations_row[0])
    else:
        cites = compute_self_citations(recid, tags)
        sql = "REPLACE INTO rnkSELFCITES (`id`, `count`, `references`," \
                    " `last_updated`) VALUES(%s, %s, %s, NOW())"
        references_string = ','.join(str(r) for r in references)
        run_sql(sql, (recid, len(cites), references_string))
        if verbose:
            write_message("%s found" % len(cites))


def rebuild_tables():
    task_update_progress('emptying tables')
    empty_self_cites_tables()
    task_update_progress('filling tables')
    fill_self_cites_tables()
    return True


def fetch_bibauthorid_last_update():
    bibauthorid_log = bibauthorid_user_log(userinfo='daemon',
                                       action='PFAP',
                                       only_most_recent=True)
    try:
        bibauthorid_end_date = bibauthorid_log[0][2]
    except IndexError:
        bibauthorid_end_date = datetime(year=1, month=1, day=1)

    return bibauthorid_end_date


def fetch_last_updated(name=NAME):
    """Fetch last runtime of given task"""
    end_date = get_bibrankmethod_lastupdate('citation')

    if CFG_SELFCITES_USE_BIBAUTHORID:
        bibauthorid_end_date = fetch_bibauthorid_last_update()
        end_date = min(end_date, bibauthorid_end_date)

    select_sql = "SELECT last_updated, last_id FROM xtrJOB" \
                 " WHERE name = %s LIMIT 1"
    row = run_sql(select_sql, (name,))
    if not row:
        sql = "INSERT INTO xtrJOB (name, last_updated, last_id) " \
              "VALUES (%s, NOW(), 0)"
        run_sql(sql, (name,))
        row = run_sql(select_sql, (name,))

    # Fallback in case we receive None instead of a valid date
    start_date = row[0][0] or datetime(year=1, month=1, day=1)
    start_id   = row[0][1]

    return start_id, start_date, end_date


def store_last_updated(recid, date, name=NAME):
    """Store the date of the latest daemon run"""
    sql = "UPDATE xtrJOB SET last_updated = %s, last_id = %s " \
                "WHERE name=%s AND last_updated <= %s"
    iso_date = date.isoformat()
    run_sql(sql, (iso_date, recid, name, iso_date))



def skip_already_processed_records(records, start_id, start_date):
    """Pop items that have been processed from the records array

    Handles the case when more records have the same timestamp
    and we stopped in the middle of them.

    The records need to be ordered for this method to work or we would
    skip random records.
    """
    for i, recid in enumerate(r for r, date in records if date == start_date):
        if recid == start_id:
            return records[i + 1:]
    return records


def fetch_concerned_records():
    """Fetch records specified by the task options

    Usually recently created/modified records
    or a list of ids specified via the command line
    """
    task_update_progress("Fetching record ids")

    start_id, start_date, end_date = fetch_last_updated()

    # Below, we use <= because oaiharvest introduces more than one record with
    # the same timestamp as a result we need to reprocess all of them
    # if we stopped in the middle (to not miss some of them)
    if task_get_option('new'):
        # Fetch all records inserted since last run
        sql = "SELECT `id`, `creation_date` FROM `bibrec` " \
            "WHERE `creation_date` >= %s " \
            "AND `creation_date` <= %s " \
            "ORDER BY `creation_date`" \
            "LIMIT 5000"
        records = run_sql(sql, (start_date.isoformat(), end_date.isoformat()))
        records = skip_already_processed_records(records, start_id, start_date)

    elif task_get_option('modified'):
        # Fetch all records modified since last run
        sql = "SELECT `id`, `modification_date` FROM `bibrec` " \
            "WHERE `modification_date` >= %s " \
            "AND `modification_date` <= %s " \
            "ORDER BY `modification_date`" \
            "LIMIT 5000"
        records = run_sql(sql, (start_date.isoformat(), end_date.isoformat()))
        records = skip_already_processed_records(records, start_id, start_date)

    else:
        recids = task_get_option('recids')
        for collection in task_get_option('collections'):
            recids.add(get_collection_reclist(collection))
        format_strings = ','.join(['%s'] * len(recids))
        records = run_sql("SELECT `id`, NULL FROM `bibrec` " \
            "WHERE `id` IN (%s) ORDER BY `id`" % format_strings,
                list(recids))

    task_update_progress("Done fetching record ids")

    return records


def catch_exceptions(f):
    def fun():
        try:
            return f()
        except:
            # Remove extra '\n'
            write_message(traceback.format_exc()[:-1])
            raise
    return fun


@catch_exceptions
def task_run_core():
    """
    This is what gets executed first when the task is started.
    It handles the --rebuild option. If that option is not specified
    we fall back to the process_one()
    """
    if task_get_option('rebuild'):
        return rebuild_tables()

    write_message("Starting")

    tags = get_authors_tags()
    records = fetch_concerned_records()

    total = len(records)
    for count, (recid, date) in enumerate(records):
        task_sleep_now_if_required(can_stop_too=True)
        msg = "Extracting for %s (%d/%d)" % (recid, count + 1, total)
        task_update_progress(msg)
        write_message(msg)

        process_one(recid, tags)

        if date:
            store_last_updated(recid, date)

    write_message("Complete")
    return True


def process_one(recid, tags):
    """Self-cites core func, executed on each recid"""
    update_self_cites_tables(recid, tags)
    compute_and_store_self_citations(recid, tags)

    references = get_refers_to(recid)
    for recordid in references:
        compute_and_store_self_citations(recordid, tags)


def empty_self_cites_tables():
    """
    This will empty all the self-cites tables

    The purpose is to rebuild the tables from scratch in case there is problem
    with them: inconsitencies, corruption,...
    """
    run_sql('TRUNCATE rnkRECORDSCACHE')
    run_sql('TRUNCATE rnkEXTENDEDAUTHORS')
    run_sql('TRUNCATE rnkSELFCITES')


def fill_self_cites_tables():
    """
    This will fill the self-cites tables with data

    The purpose of this function is to fill these tables on a website that
    never ran the self-cites daemon
    """
    tags = get_authors_tags()
    all_ids = [r[0] for r in run_sql('SELECT id FROM bibrec ORDER BY id')]
    # Fill intermediary tables
    for index, recid in enumerate(all_ids):
        if index % 1000 == 0:
            task_update_progress('intermediate %d/%d' % (index, len(all_ids)))
            task_sleep_now_if_required()
        update_self_cites_tables(recid, tags)
    # Fill self-cites table
    for index, recid in enumerate(all_ids):
        if index % 1000 == 0:
            task_update_progress('final %d/%d' % (index, len(all_ids)))
            task_sleep_now_if_required()
        compute_and_store_self_citations(recid, tags)


def main():
    """Constructs the refextract bibtask."""
    # Build and submit the task
    task_init(authorization_action='runrefextract',
        authorization_msg="Refextract Task Submission",
        description=DESCRIPTION,
        # get the global help_message variable imported from refextract.py
        help_specific_usage=HELP_MESSAGE,
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("hVv:x:r:c:naim", [
                            "help",
                            "version",
                            "verbose=",
                            "recids=",
                            "collections=",
                            "new",
                            "modified",
                            "rebuild"]),
        task_submit_elaborate_specific_parameter_fnc=parse_option,
        task_submit_check_options_fnc=check_options,
        task_run_fnc=task_run_core)
