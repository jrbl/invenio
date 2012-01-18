# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Initialise Refextract task"""

import sys
import os
import time
import traceback
from shutil import copyfile
from tempfile import mkstemp
from datetime import datetime

from invenio.bibtask import task_init, task_set_option, \
                            task_get_option, write_message, \
                            task_has_option, task_get_task_param, \
                            task_sleep_now_if_required, \
                            task_update_progress
from invenio.config import CFG_VERSION, CFG_TMPDIR, CFG_BINDIR, CFG_ETCDIR
from invenio.dbquery import run_sql
## Used to create a new record object, to obtain fulltexts
from invenio.bibdocfile import BibRecDocs
## Used to obtain the fulltexts for a given collection
from invenio.search_engine import get_collection_reclist
## Help message is the usage() print out of how to use Refextract
from invenio.authorextract_cli import help_message, description
from invenio import authorextract_engine
from invenio.config import CFG_PATH_GFILE


class TaskNotFound(Exception):
    pass


def split_ids(value):
    return [c.strip() for c in value.split(',') if c.strip()]


def fetch_last_updated(name='refextract'):
    select_sql = "SELECT last_id, last_updated FROM xtrJOB" \
        " WHERE name = %s LIMIT 1"
    row = run_sql(select_sql, (name,))
    if not row:
        sql = "INSERT INTO xtrJOB (name, last_updated, last_id) " \
            "VALUES (%s, NOW(), 0)"
        run_sql(sql, (name,))
        row = run_sql(select_sql, (name,))

    # Fallback in case we receive None instead of a valid date
    last_id   = row[0][0] or 0
    last_date = row[0][1] or datetime(year=1, month=1, day=1)

    return last_id, last_date


def store_last_updated(recid, creation_date, name='refextract'):
    sql = "UPDATE xtrJOB SET last_id = %s, last_updated = %s WHERE name=%s"
    row = run_sql(sql, (recid, creation_date.isoformat(), name))


def task_run_core():
    """calls extract_references in refextract"""
    # This changes the behavior or write_message, task_update_progress
    # and halt
    refextract_engine.RUNNING_INDEPENDENTLY = False

    write_message("Starting references extraction.")
    task_update_progress("fetching record ids")

    last_id, last_date = fetch_last_updated()

    if task_get_option('new'):
        ## Fetch all records inserted since last run
        sql = "SELECT id, creation_date FROM bibrec " \
            "WHERE creation_date >= %s " \
            "AND id > %s " \
            "ORDER BY `creation_date`"
        records = run_sql(sql, (last_date.isoformat(), last_id))
    else:
        recids = task_get_option('recids')
        for collection in task_get_option('collections'):
            recids.add(get_collection_reclist(collection))
        format_strings = ','.join(['%s'] * len(recids))
        records = run_sql("SELECT `id`, `creation_date` FROM `bibrec` " \
            "WHERE `id` IN (%s) ORDER BY `creation_date`" % format_strings,
                list(recids))

    count = 1
    total = len(records)
    for recid, creation_date in records:
        task_sleep_now_if_required(can_stop_too=True)
        msg = "Extracting references for %s (%d/%d)" % (recid, count, total)
        task_update_progress(msg)
        write_message(msg)
        try:
            update_references(recid, task_get_option('inspire'))
            write_message("Extracted references for %s" % recid)
        except FullTextNotAvailable:
            write_message("No full text available for %s" % recid)
        store_last_updated(recid, creation_date)
        count += 1

    write_message("Reference extraction complete.")

    return True


def parse_option():
    """ Reimplement this method for having the possibility to check options
    before submitting the task, in order for example to provide default
    values. It must return False if there are errors in the options.
    """
    if not task_get_option('new') and not task_get_option('recids') \
                and not task_get_option('collections'):
        print >>sys.stderr, 'Error: No input file specified, you need' \
            ' to specify which files to run on'
        return False

    return True


def check_options(key, value, opts, args):
    """ Must be defined for bibtask to create a task """
    if args and len(args) > 0:
        ## There should be no standalone arguments for any refextract job
        ## This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-a', '--new'):
        task_set_option('new', True)
    elif key in ('-p', '--inspire'):
        task_set_option('inspire', True)
    elif key in ('-j', '--kb-journal'):
        task_set_option('kb-journal', value)
    elif key in ('-n', '--kb-report-number'):
        task_set_option('kb-report-number', value)
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


def main():
    """Constructs the refextract bibtask."""
    ## Build and submit the task
    task_init(authorization_action='runrefextract',
        authorization_msg="Refextract Task Submission",
        description=description,
        # get the global help_message variable imported from refextract.py
        help_specific_usage=help_message + """
Scheduled (daemon) Refextract options:
  -a, --new          Run on all newly inserted records.
  -r, --recids       Record id for extraction.
  -c, --collections  Entire Collection for extraction.

  Examples:
   (run a daemon job)
      refextract -a
   (run as standalone)
      refextract -x /home/chayward/refs.xml -f /home/chayward/thesis.pdf

""",
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("hVv:zr:x:d:pj:n:c:e:f:na",
                            ["help",
                             "version",
                             "verbose=",
                             "authors",
                             "affiliations",
                             "xmlfile=",
                             "inspire",
                             "recids=",
                             "collections=",
                             "new"]),
        task_submit_elaborate_specific_parameter_fnc=parse_option,
        task_submit_check_options_fnc=check_options,
        task_run_fnc=task_run_core)
