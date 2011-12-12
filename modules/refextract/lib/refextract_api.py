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

"""This is where all the public API calls are accessible

This is the only file containing public calls and everything that is
present here can be considered private by the invenio modules.
"""


import os

from urllib import urlretrieve
from tempfile import mkstemp

from refextract_engine import parse_references, \
    get_plaintext_document_body, extract_references_from_fulltext

from invenio.bibdocfile import BibRecDocs, InvenioWebSubmitFileError
from invenio.bibedit_utils import get_record
from invenio.bibtask import task_low_level_submission
from invenio.bibrecord import record_delete_fields, record_xml_output, \
    create_record, record_get_field_instances, record_add_fields, \
    record_has_field
from invenio.refextract_config import CFG_REFEXTRACT_FILENAME
from invenio.config import CFG_TMPSHAREDDIR


class FullTextNotAvailable(Exception):
    """Raised when we cannot access the document text"""


class RecordHasReferences(Exception):
    """Raised when
    * we asked to updated references for a record
    * we explicitely asked for not overwriting references for this record
      (via the appropriate function argument)
    * the record has references thus we cannot update them
   """


def extract_references_from_url_xml(url):
    """Extract references from the pdf specified in the url

    The single parameter is the path to the pdf.
    It raises FullTextNotAvailable if the url gives a 404
    The result is given in marcxml.
    """
    filename, _ = urlretrieve(url)
    try:
        try:
            marcxml = extract_references_from_file_xml(filename)
        except IOError, err:
            if err.code == 404:
                raise FullTextNotAvailable()
            else:
                raise
    finally:
        os.remove(filename)
    return marcxml


def extract_references_from_file_xml(path, recid=1, inspire=False):
    """Extract references from a local pdf file

    The single parameter is the path to the file
    It raises FullTextNotAvailable if the file does not exist
    The result is given in marcxml.
    """
    if not os.path.isfile(path):
        raise FullTextNotAvailable()

    docbody, _ = get_plaintext_document_body(path)
    reflines, _, _ = extract_references_from_fulltext(docbody)
    if not len(reflines):
        docbody, _ = get_plaintext_document_body(path, keep_layout=True)
        reflines, _, _ = extract_references_from_fulltext(docbody)

    return parse_references(reflines, recid=recid, inspire=inspire)


def extract_references_from_string_xml(source, inspire=False):
    """Extract references from a string

    The single parameter is the document
    The result is given in marcxml.
    """
    docbody = source.split('\n')
    reflines, _, _ = extract_references_from_fulltext(docbody)
    return parse_references(reflines, inspire=inspire)


def extract_references_from_record_xml(recid, inspire=False):
    """Extract references from a record id

    The single parameter is the document
    The result is given in marcxml.
    """
    rec_info = BibRecDocs(recid)
    docs = rec_info.list_bibdocs()

    path = False
    for doc in docs:
        try:
            path = doc.get_file('pdf').get_full_path()
        except InvenioWebSubmitFileError:
            try:
                path = doc.get_file('pdfa').get_full_path()
            except InvenioWebSubmitFileError:
                continue

    if not path:
        raise FullTextNotAvailable()

    return extract_references_from_file_xml(path, recid=recid, inspire=inspire)


def replace_references(recid, inspire=False):
    """Replace references for a record

    The record itself is not updated, the marc xml of the document with updated
    references is returned

    Parameters:
    * recid: the id of the record
    * inspire: format of ther references
    """
    # Parse references
    references_xml = extract_references_from_record_xml(recid, inspire=inspire)
    references = create_record(references_xml.encode('utf-8'))
    # Record marc xml
    record = get_record(recid)

    if references[0]:
        fields_to_add = record_get_field_instances(references[0],
                                                   tag='999',
                                                   ind1='%',
                                                   ind2='%')
        # Replace 999 fields
        record_delete_fields(record, '999')
        record_add_fields(record, '999', fields_to_add)
        # Update record references
        out_xml = record_xml_output(record)
    else:
        out_xml = None

    return out_xml


def update_references(recid, inspire=False, overwrite=True):
    """Update references for a record

    First, we extract references from a record.
    Then, we are not updating the record directly but adding a bibupload
    task in -c mode which takes care of updating the record.
    
    Parameters:
    * recid: the id of the record
    * inspire: format of ther references
    """

    if not overwrite:
        # Check for references in record
        record = get_record(recid)
        if record and record_has_field(record, '999'):
            raise RecordHasReferences(recid)

    # Parse references
    references_xml = extract_references_from_record_xml(recid, inspire=inspire)

    # Save new record to file
    (temp_fd, temp_path) = mkstemp(prefix=CFG_REFEXTRACT_FILENAME,
                                   dir=CFG_TMPSHAREDDIR)
    temp_file = os.fdopen(temp_fd, 'w')
    temp_file.write(references_xml.encode('utf-8'))
    temp_file.close()

    # Update record
    task_low_level_submission('bibupload', 'refextract', '-P', '5',
                              '-c', temp_path)


def record_has_fulltext(recid):
    """Checks if we can access the fulltext for the given recid"""
    rec_info = BibRecDocs(recid)
    docs = rec_info.list_bibdocs()

    path = None
    for doc in docs:
        try:
            path = doc.get_file('pdf').get_full_path()
        except InvenioWebSubmitFileError:
            try:
                path = doc.get_file('pdfa').get_full_path()
            except InvenioWebSubmitFileError:
                continue

    return path is not None
