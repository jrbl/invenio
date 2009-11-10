#!/usr/bin/env python

from invenio.search_engine import search_pattern, print_record
from invenio.bibrecord import create_record, record_get_field_values, record_get_field_value


def auPairs(recID):
    yieldedSomething = False
    record = create_record(print_record(recID, 'xm'))[0]
    
    def extract(l):
        a = None
        u = None
        for key, val in l:
            if key == 'a':
                a = val
            elif key == 'u':
                u = val
        return a, u

    try:
        yield extract( record['100'][0][0] )
        yieldedSomething = True
    except KeyError:
        pass
    except TypeError, msg:
        print "ERROR: TypError in\nrecID = %s\nrec = %s\n%s" % (recID, record, msg)

    try:
        fields = record['700']
    except KeyError:
        if not yieldedSomething:
            yield None, None
        return

    for fieldline in fields:
        tuplist = fieldline[0]
        yield extract( tuplist )

def name2affils(name, skip_id):
    """Given an author name pattern, find all possible prior affiliations""" 

    previousGood = None

    search_results = sorted( search_pattern( p=name, ap=1 ), reverse=True )

    for recID in search_results:
        if recID == skip_id: continue
        for author, affiliation in auPairs(recID):
            if author == None: break
            if name.lower() in author.lower():
                if affiliation != None:
                    previousGood = affiliation
                    yield recID, author, affiliation
                else:
                    yield recID, author, previousGood

def recid2names(id):
    for author, junk in auPairs(id):
        yield author

def flattenByCounts(l, histogram=False):
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
        else: return 0

    counts = {}
    for item in l:
        if item not in counts:
            counts[item] = l.count(item)
    if not histogram:
        return sorted(counts.keys(), cmp=freq_sort)
    return sorted([(key, counts[key]) for key in counts], cmp=freq_sort)
        

if __name__ == "__main__":
    """Exploratory test harness"""

    import sys

    search_for = '12'
    if len(sys.argv) > 1:
        search_for = sys.argv[1]

    search_names = recid2names(search_for)

    for name in search_names:
        for recID, auth, affil in name2affils(name, search_for):
            if affil != None:
                print '\t%5d %35s %35s' % (recID, '"'+auth+'"', '"'+affil+'"')

