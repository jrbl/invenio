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

import re


def massage_arxiv_reportnumber(report_number):
    """arXiv report numbers need some massaging
        to change from arXiv-1234-2233(v8) to arXiv.1234.2233(v8)
              and from arXiv1234-2233(v8) to arXiv.1234.2233(v8)
    """
    ## in coming report_number should start with arXiv
    if report_number.find('arXiv') != 0 :
        return report_number
    words = report_number.split('-')
    if len(words) == 3:  ## case of arXiv-yymm-nnnn  (vn)
        words.pop(0) ## discard leading arXiv
        report_number = 'arXiv:' + '.'.join(words).lower()
    elif len(words) == 2: ## case of arXivyymm-nnnn  (vn)
        report_number = 'arXiv:' + words[0][5:] + '.' + words[1].lower()

    report_number = re.sub(ur'(arXiv\.\d{4}\.\d{4})(\(v\d\)|v\d)',
                           ur'\g<1>',
                           report_number,
                           re.UNICODE)

    return report_number
