# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

import argparse

description = ""

# Help message, used by bibtask's 'task_init()' and 'usage()'
help_message = """
  -a, --authors        extract the authors of the document. Attempt to
                       return associations between authors and affiliations
                       whenever possible.
  -l, --affiliations
                       extract affiliations from the document.

Standalone AuthorExtract options:
  --first_author       use the following regexp as the first author, helps for
                       author extraction, ignored otherwise
  -z, --raw_authors
                       Treat the input file as the search space. i.e. skip the
                       stage of trying to locate the reference/top section within a
                       document and instead move to the stage of recognition
                       and standardisation of citations within lines, and the
                       extraction of authors.
"""

def get_cli_options():
    """Get the various arguments and options from the command line and populate
       a dictionary of cli_options.
       @return: (tuple) of 2 elements. First element is a dictionary of cli
        options and flags, set as appropriate; Second element is a list of cli
        arguments.
    """
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-f', '--fulltext', action='append')
    parser.add_argument('-a', '--authors', action='store_true')
    parser.add_argument('-l', '--affiliations', action='store_true')
    parser.add_argument('--raw_authors', action='store_true')
    parser.add_argument('--first_author')

    return parser.parse_args()


def main(config):
    pass