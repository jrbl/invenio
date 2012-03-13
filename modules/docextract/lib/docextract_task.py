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

"""Generic Framework for extracting metadata from records using bibsched"""

import traceback
from itertools import chain
from datetime import datetime
from invenio.bibtask import task_get_option, write_message, \
                            task_sleep_now_if_required, \
                            task_update_progress
from invenio.dbquery import run_sql
from invenio.search_engine import get_collection_reclist

def task_run_core_wrapper(name, core_func, extra_vars=None):
    """
    Wraps task main function in order to display a traceback in case of error
    """
    def fun():
        try:
            return task_run_core(name, core_func, extra_vars)
        except Exception:
            # Remove extra '\n'
            write_message(traceback.format_exc()[:-1])
            raise
    return fun


def fetch_last_updated(name):
    """Fetch last runtime of given task"""
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


def store_last_updated(recid, creation_date, name):
    """Store the date of the latest daemon run"""
    sql = "UPDATE xtrJOB SET last_id = %s WHERE name=%s AND last_id < %s"
    run_sql(sql, (recid, name, recid))
    sql = "UPDATE xtrJOB SET last_updated = %s " \
                "WHERE name=%s AND last_updated < %s"
    iso_date = creation_date.isoformat()
    run_sql(sql, (iso_date, name, iso_date))


def fetch_concerned_records(name):
    """
    Fetch records specified by the task options
    Usually recently created/modified records
    or a list of ids specified via the command line
    """
    task_update_progress("Fetching record ids")

    last_id, last_date = fetch_last_updated(name)

    if task_get_option('new'):
        # Fetch all records inserted since last run
        sql = "SELECT `id`, `creation_date` FROM `bibrec` " \
            "WHERE `creation_date` >= %s " \
            "AND `id` > %s " \
            "ORDER BY `creation_date`" \
            "LIMIT 5000"
        records = run_sql(sql, (last_date.isoformat(), last_id))
    elif task_get_option('modified'):
        # Fetch all records inserted since last run
        sql = "SELECT `id`, `modification_date` FROM `bibrec` " \
            "WHERE `modification_date` >= %s " \
            "AND `id` > %s " \
            "ORDER BY `modification_date`" \
            "LIMIT 5000"
        records = run_sql(sql, (last_date.isoformat(), last_id))
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


def task_run_core(name, func, extra_vars=None):
    """Calls extract_references in refextract"""
    write_message("Starting")

    records = fetch_concerned_records(name)

    count = 1
    total = len(records)
    for recid, date in records:
        task_sleep_now_if_required(can_stop_too=True)
        msg = "Extracting for %s (%d/%d)" % (recid, count, total)
        task_update_progress(msg)
        write_message(msg)
        if extra_vars:
            func(recid, **extra_vars)
        else:
            func(recid)
        if date:
            store_last_updated(recid, date, name)
        count += 1

    write_message("Complete")
    return True


def split_ids(value):
    """
    Split ids given in the command line
    Possible formats are:
    * 1
    * 1,2,3,4
    * 1-5,20,30,40
    Returns respectively
    * set([1])
    * set([1,2,3,4])
    * set([1,2,3,4,5,20,30,40])
    """
    def parse(el):
        el = el.strip()
        if not el:
            ret = []
        elif '-' in el:
            start, end = el.split('-', 1)
            ret = xrange(int(start), int(end) + 1)
        else:
            ret = [int(el)]
        return ret
    return chain(*(parse(c) for c in value.split(',') if c.strip()))

