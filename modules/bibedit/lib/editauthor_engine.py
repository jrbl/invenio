#!/usr/bin/env python
"""Utility functions to ease the manipulation of records."""

from invenio.search_engine import search_pattern, print_record
from invenio.bibrecord import create_record


def auPairs(recid):
    """Generate [author, affiliation ...] lists for input record id."""
    yieldedSomething = False
    record = create_record(print_record(recid, 'xm'))[0]

    def extract(lst):
        """Helper builds individual [author, affil ...] lists."""
        value = [None]
        for code, text in lst:
            if code == 'a':
                value[0] = text
            elif code == 'u':
                value.append(text)
        return value

    try:
        yield extract(record['100'][0][0])
        yieldedSomething = True
    except KeyError:
        pass
    except TypeError, msg:
        print "ERROR: TypError in\nrecid = %s\nrec = %s\n%s" % \
              (recid, record, msg)

    try:
        fields = record['700']
    except KeyError:
        if not yieldedSomething:
            yield None, None
        return

    for fieldline in fields:
        tuplist = fieldline[0]
        yield extract(tuplist)


def name2affils(name, skip_id):
    """Given an author name pattern, find all possible prior affiliations"""

    prev_good = None

    search_results = sorted(search_pattern(p=name, ap=1), reverse=True)

    for recid in search_results:
        if recid == skip_id:
            continue
        for author_list in auPairs(recid):
            if author_list[0] == None:
                break
            if name.lower() in author_list[0].lower():
                if len(author_list) > 1:
                    prev_good = author_list[1]
                    yield recid, author_list[0], author_list[1:]
                else:
                    yield recid, author_list[0], [prev_good]


def recid2names(recid):
    """Given a record ID, generate a list of authors' names."""
    for author_list in auPairs(recid):
        yield author_list[0]


def flattenByCounts(lst, histogram=False):
    """Build a list sorted by frequency.

    @param l: a list of items with possible repetitions
    @param histogram: if True, return list is (item, count) pairs
    @return: a list without repetitions, items sorted by frequency
    """

    def freq_sort(a, b):
        if counts[a] < counts[b]:
            return 1
        elif counts[b] < counts[a]:
            return -1
        else:
            return 0

    counts = {}
    for item in lst:
        if item not in counts:
            counts[item] = lst.count(item)
    if not histogram:
        return sorted(counts.keys(), cmp=freq_sort)
    return sorted([(key, counts[key]) for key in counts], cmp=freq_sort)


#######################################
# Exploratory test harness
if __name__ == "__main__":

    import sys

    search_for = '12'
    if len(sys.argv) > 1:
        search_for = sys.argv[1]

    search_names = recid2names(search_for)

    for author_name in search_names:
        for recID, auth, affils in name2affils(author_name, search_for):
            if affils[0] != None:
                print '\t%5d %35s' % (recID, '"'+auth+'"'),
                for affil in affils:
                    print '%35s' % '"' + affil + '"',
                print
