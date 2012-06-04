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
Citations Stats Task

Recomputes the global citesummary (typically every 24 hours)
"""

import os
import md5

from invenio.bibtask import task_init, write_message
from invenio.config import CFG_VERSION
from invenio.search_engine_summarizer import summarize_records
from invenio.search_engine import search_pattern
from invenio.webdoc_info_webinterface import perform_request_save_file

DESCRIPTION = ""

HELP_MESSAGE = """
  Examples:
   (run a daemon job)
      refextract -s 24h
"""


# def check_options():
#     """Reimplement this method for having the possibility to check options
#     before submitting the task, in order for example to provide default
#     values. It must return False if there are errors in the options.
#     """
#     return True


# def parse_option(key, value, opts, args):
#     """ Must be defined for bibtask to create a task """
#     return True


def task_run_core():
    write_message('generating global citesummary')
    recids = search_pattern('collection:citable')
    html = summarize_records(recids, of='hcs', ln='en')
    write_message('md5: %s' % md5.new(html).hexdigest())
    r = perform_request_save_file(filename='/hep/citation-stats.webdoc',
                                  filecontent=html)
    success = r['status'] == 'save_success'
    if not success:
        write_message('status: %s' % r['status'])
    return success


def main():
    """Constructs the bibtask."""

    # Build and submit the task
    task_init(authorization_action='runcitationsstatstask',
        authorization_msg="Citations Stats Task Submission",
        description=DESCRIPTION,
        help_specific_usage=HELP_MESSAGE,
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("", []),
        # task_submit_elaborate_specific_parameter_fnc=parse_option,
        # task_submit_check_options_fnc=check_options,
        task_run_fnc=task_run_core
    )
