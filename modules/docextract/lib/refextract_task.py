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

"""
Refextract task

Sends references to parse through bibsched
"""

import sys
import traceback
from datetime import datetime

from invenio.bibtask import task_init, task_set_option, \
                            task_get_option, write_message, \
                            task_sleep_now_if_required, \
                            task_update_progress
from invenio.config import CFG_VERSION, CFG_INSPIRE_SITE

from invenio.dbquery import run_sql
# Used to obtain the fulltexts for a given collection
from invenio.search_engine import get_collection_reclist
# Help message is the usage() print out of how to use Refextract
from invenio.refextract_cli import HELP_MESSAGE, DESCRIPTION
from invenio.refextract_api import update_references, \
                                   FullTextNotAvailable, \
                                   RecordHasReferences
from invenio.docextract_task import task_run_core_wrapper


def split_ids(value):
    return [c.strip() for c in value.split(',') if c.strip()]


def check_options():
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


def parse_option(key, value, opts, args):
    """ Must be defined for bibtask to create a task """
    if args and len(args) > 0:
        # There should be no standalone arguments for any refextract job
        # This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-a', '--new'):
        task_set_option('new', True)
        task_set_option('no-overwrite', True)
    elif key in ('-i', '--inspire'):
        task_set_option('inspire', True)
    elif key in ('--kb-reports'):
        task_set_option('kb-reports', value)
    elif key in ('--kb-journals'):
        task_set_option('kb-journals', value)
    elif key in ('--kb-journals-re'):
        task_set_option('kb-journals-re', value)
    elif key in ('--kb-authors'):
        task_set_option('kb-authors', value)
    elif key in ('--kb-books'):
        task_set_option('kb-books', value)
    elif key in ('--kb-conferences'):
        task_set_option('kb-conferences', value)
    elif key in ('--no-overwrite'):
        task_set_option('no-overwrite', True)
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


def task_run_core(recid):
    if task_get_option('inspire'):
        inspire = True
    else:
        inspire = CFG_INSPIRE_SITE

    try:
        update_references(recid,
                          inspire=inspire,
                          overwrite=not task_get_option('no-overwrite'))
        write_message("Extracted references for %s" % recid)
    except FullTextNotAvailable:
        write_message("No full text available for %s" % recid)
    except RecordHasReferences:
        write_message("Record %s has references, skipping" % recid)


def main():
    """Constructs the refextract bibtask."""
    # Build and submit the task
    task_init(authorization_action='runrefextract',
        authorization_msg="Refextract Task Submission",
        description=DESCRIPTION,
        # get the global help_message variable imported from refextract.py
        help_specific_usage=HELP_MESSAGE + """
  Scheduled (daemon) Refextract options:
  -a, --new          Run on all newly inserted records.
  -m, --modified     Run on all newly modified records.
  -r, --recids       Record id for extraction.
  -c, --collections  Entire Collection for extraction.

  Examples:
   (run a daemon job)
      refextract -a
   (run on a set of records)
      refextract --recids 1,2 -r 3
   (run on a collection)
      refextract --collections "Reports"
   (run as standalone)
      refextract -o /home/chayward/refs.xml /home/chayward/thesis.pdf

""",
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("hVv:x:r:c:nai",
                            ["help",
                             "version",
                             "verbose=",
                             "inspire",
                             "kb-journals=",
                             "kb-journals-re=",
                             "kb-report-numbers=",
                             "kb-authors=",
                             "kb-books=",
                             "recids=",
                             "collections=",
                             "new",
                             "modified",
                             "no-overwrite"]),
        task_submit_elaborate_specific_parameter_fnc=parse_option,
        task_submit_check_options_fnc=check_options,
        task_run_fnc=task_run_core_wrapper('refextract', task_run_core))
