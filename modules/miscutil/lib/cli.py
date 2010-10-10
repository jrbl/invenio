#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########+#########+#########+#########+#########+#########+#########+#########
# Copyright (C) 2010  SLAC National Accelerator Laboratory
#
#This program is free software: you can redistribute it and/or modify it under
#the terms of the GNU General Public License as published by the Free Software
#Foundation, either version 3 of the License, or (at your option) any later
#version.
#
#This program is distributed in the hope that it will be useful, but WITHOUT
#ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#details.
#
#You should have received a copy of the GNU General Public License along with
#this program.  If not, see <http://www.gnu.org/licenses/>.
"""cli: Load this into ipython to make interactive Invenio use nicer

cli is an Invenio module intended to make working with Invenio interactively
(for example, for exploratory bibliometrics) a lot more comfortable.
"""

import invenio
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_record, get_fieldvalues
from invenio.bibrank_citation_searcher import get_citation_dict as pre_get_citation_dict
from invenio.bibformat import format_record
from invenio.bibformat import format_records
from invenio.intbitset import intbitset
from invenio.bibformat_dblayer import get_tags_from_name

FORWARD_CITATION_DICTIONARY = None


def get_citation_dict():
    global FORWARD_CITATION_DICTIONARY
    if FORWARD_CITATION_DICTIONARY == None:
        FORWARD_CITATION_DICTIONARY = pre_get_citation_dict('citationdict')
    return FORWARD_CITATION_DICTIONARY

def get_cite_counts(query = ''):
    """Generate the recid, citation count pairs for recids with cites >= 1.

    If query is given, gives counts for recids in search results.
    If query is empty, gives counts for all recids (default)

    Sample Usage:
    [x for x in cli.get_cite_counts('recid:95')]
    results in:
    [(95, 2)]
    """
    for recid in perform_request_search(p=query):
        yield recid, get_cite_count(recid)

def get_cite_count(recid):
    cites = get_citation_dict()
    if cites.has_key(recid):
        return len(cites[recid])
    else:
        return 0

def irn(recid):
    """Return the first (only) IRN of a given recid, or None"""
    irnlist = get_fieldvalues(recid, '970__a')
    if len(irnlist) > 0:
        return irnlist[0]
    else:
        return None

def field(recid, name):
    """Return the first value of the field corresponding to the given tag
    name in the given recid, or None"""
    datalist = fields(recid, name)
    if len(datalist) > 0:
        return datalist[0]
    else:
        return None

def fields(recid, name):
    """Return the list of values of the field corresponding to the given tag
    name in the given recid, or None"""
    fields = get_tags_from_name(name)
    if len(fields) > 0:
        return(get_fieldvalues(recid, fields[0]))
    else:
        return None

if __name__ == "__main__":
    """FIXME: As a command, cli should either run its unit tests, or invoke ipython"""
    pass
