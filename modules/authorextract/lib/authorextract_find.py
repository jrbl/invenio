# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

import re
from invenio.docextract_utils import write_message


def find_author_section(docbody, author_marker=None, first_author=None):
    """Search in document body for its author section.
       Looks top down for things that look like an author list.  This will
       work generally poorly unless one is using the LaTeX in some way, or
       if one knows the first author. Both of these methods are tried
       first, falling back to a default search for the first line
       matching
          [A-Z]\w+, [A-Z]\.?\s?[A-Z]?\.?\s?\d*
          (i.e. a word starting with caps, followed by comma, space, one
          or two initials with possible periods and then possibly a number.
    
       @param docbody: (list) of strings - the full document body.
       @param author_marker: (string) optional (regexp) marker embedded by latex
       for beginning and end of author section  
       @param first_author: (string) optional (regexp) first author to help find
       beginning of section
       @return: (dictionary) :
          { 'start_line' : (integer) - index in docbody of 1st author line,
            'end_line' : (integer) - index of last author line
          }
                 Much of this information is used by later functions to rebuild
                 a reference section.
         -- OR --
                (None) - when the reference section could not be found.
    """
    auth_start_line = None
    auth_end_line = None
    # A pattern to match author names
    # demands name has a comma
    # allows space or hyphen in family name
    # allows only initials (capital letters) but allows many (3 or more if
    #        no . or spaces used...)
    # allows a trailing number
    # Aubert, F. I. 3
    author_pattern = re.compile(ur'([A-Z]\w+\s?\w+)\s?([A-Z\.\s]{1,9})\.?\s?(\d*)', re.UNICODE)
    # F. I. Aubert, 3
    author_pattern = re.compile(ur'([A-Z])\.\s?([A-Z]?)\.?\s?([A-Z]\w+\s?\w*)\,?\s?(\d*)', re.UNICODE)
    start_pattern = author_pattern
    end_pattern = author_pattern

    # if author_marker is not None:
    #    start_pattern = re.compile(author_marker+'(.*)')
    #    end_pattern = re.compile('(.*)'+author_marker)
    # if first_author is not None:
    #    start_pattern = re.compile(first_author)
    #    end_pattern = None;

    for position in range(len(docbody)):
        line = docbody[position]
        if auth_start_line is None:
            write_message("examining " + line.encode("utf8"), verbose=2)
            write_message("re -> " + start_pattern.pattern, verbose=2)
            if start_pattern.search(line):
                auth_start_line = position
        elif auth_end_line is None and end_pattern.search(line):
            # this could be the last author or one of many
            auth_end_line = position
        elif auth_end_line is not None and end_pattern.search(line):
            break
            # leave when we have found a possible and, and the ending
            # pattern no longer matches this will fail if there are
            # affiliations interspersed, or othe corruptions of the list

    if auth_start_line is not None:
        ## return dictionary containing details of author section:
        auth_sect_details = {
            'start_line'             : auth_start_line,
            'end_line'               : auth_end_line,
            'marker_pattern'         : author_pattern,
            'title_string'           : None,
            'marker'                 : None,
            'title_marker_same_line' : None,
        }
    else:
        auth_sect_details = None

    return auth_sect_details
 