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

from invenio.authorextract_find import find_author_section
from invenio.docextract_text import remove_page_boundary_lines, \
                                    document_contains_text, \
                                    get_page_break_positions, \
                                    get_number_header_lines, \
                                    get_number_footer_lines, \
                                    strip_headers_footers_pagebreaks


def extract_section_from_fulltext(fulltext):
    """Locate and extract a relevant named section from a fulltext document.
       Return the extracted section as a list of strings, whereby each
       string in the list is considered to be a single line (reference,
       author, abstract etc).
       E.g. a string could be something like:
        '[19] Wilson, A. Unpublished (1986).
       @param fulltext: (list) of strings, whereby each string is a line of the
       document.
       @param section: 'references', 'authors', or FIXME 'abstract'
       @return: (list) of strings, where each string is an extracted line.
    """
    # Try to remove pagebreaks, headers, footers
    fulltext = remove_page_boundary_lines(fulltext)
    # Find Section
    sect_start = find_author_section(fulltext)
    # Extract
    return get_authors_lines(fulltext,
                     sect_start["start_line"],
                     sect_end,
                     sect_start["title_string"],
                     sect_start["marker_pattern"],
                     sect_start["title_marker_same_line"])



def rebuild_author_lines(author_lines, author_pattern):
    """Given the lines that we think make up the author section reset
    everything so that each author is on one line
    """
    def found_author(matchobj):
        """ given an author in the match obj, pushes it on the stack of lines
        """
        authors.append(matchobj.group(0))
        write_message("Found author -> " + matchobj.group(0) + "\n", verbose=1)
        return ' '
    authors = []
    author_string = ' '.join(author_lines)
    author_pattern.sub(found_author, author_string)
    return authors


def get_authors_lines(docbody,
                      start_line,
                      end_line,
                      title,
                      marker_ptn,
                      title_marker_same_line):
    """Extract author lines from fulltext

    from a given section of a document extract the relevant lines, not
    including the various markers.
    @param start_line  index of docbody on which sect starts
    @param end_line   index of docbody on which sect ends
    @param title  a string that signifies the beginning
    @param marker_ptn  pattern that ids start of a line
    @param title_marker_same_line integer tells whether title and
    marker are on same line
    @param section[="references"] string denoting type of section
    @return: (list) of strings. Each string is a reference line, extracted
    from the document. """

    start_idx = start_line
    if title_marker_same_line:
        ## Title on same line as 1st ref- take title out!
        title_start = docbody[start_idx].find(title)
        if title_start != -1:
            docbody[start_idx] = docbody[start_idx][title_start + len(title):]
    elif title:
        ## Pass title line
        start_idx += 1

    ## now rebuild reference lines:
    if end_line:
        lines = docbody[start_idx:end_line+1]
    else:
        lines = docbody[start_idx:]

    return rebuild_author_lines(lines, marker_ptn)


def rebuild_author_lines(author_lines, author_pattern):
    """Given the lines that we think make up the author section reset
       everything so that each author is on one line
    """
    def found_author(matchobj):
        """ given an author in the match obj, pushes it on the stack of lines
        """
        ## Append author and remove undesirable unicode characters for this author list
        authors.append(matchobj.group(0))
        return ' '

    authors = []
    ## Kill the new line characters in the author lines
    author_string = ' '.join([x.strip() for x in author_lines])
    author_pattern.sub(found_author, author_string)
    return authors

 