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

"""AuthorExtract configuration"""


## Lines holding key matches will be replaced with the value at extraction time
CFG_REFEXTRACT_INSTITUTION_REPLACEMENTS = {
    r'^Livermore': 'LLNL, Livermore',
    r'.*?Stanford Linear Accelerator Center.*?': 'SLAC',
    r'^Fermi National Accelerator Laboratory': 'Fermilab'
}

## Lines holding these institutions will be reduced solely to the institution at extraction time
CFG_REFEXTRACT_INSTITUTION_REDUCTIONS = [
    'CERN',
    'DESY',
    'Rutherford',
    'Fermilab',
    'SLAC',
    'TRIUMF',
    'Brookhaven Livermore',
    'Argonne'
]

## The allowable distance between consecutively numerated affiliations
## A small distance value could limit the number of numerated affiliations obtained (default: 2)
CFG_REFEXTRACT_AFFILIATION_NUMERATION_ALLOWABLE_GAP = 2

## refextract author-extraction fields:
CFG_REFEXTRACT_AE_TAG_ID_HEAD_AUTHOR     = "100"  # first author-aff details
CFG_REFEXTRACT_AE_TAG_ID_TAIL_AUTHOR     = "700"  # remaining author-affs
CFG_REFEXTRACT_AE_SUBFIELD_AUTHOR        = "a"    # authors subfield
CFG_REFEXTRACT_AE_SUBFIELD_AFFILIATION   = "u"    # affiliations subfield


CFG_REFEXTRACT_MARKER_CLOSING_AFFILIATION = r"</cds.AFF>"
