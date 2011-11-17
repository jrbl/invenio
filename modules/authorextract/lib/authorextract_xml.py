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

from invenio.authorextract_config import CFG_REFEXTRACT_AE_TAG_ID_TAIL_AUTHOR


def display_auth_aff_xml_record(recid, xml_lines):
    """ Wraps XML lines holding extracted authors and affiliations
        with the necessary record and controlfield elements.
        @param recid: (int) record id of the document being extracted.
        @param xml_lines: (list) of xml holding annotated authors
        and affiliation information.
        @return: (xml_lines) xml lines with the surrounding elements.
    """
    ## Start with the opening record tag:
    out = u"%(record-open)s\n" \
              % { 'record-open' : CFG_REFEXTRACT_XML_RECORD_OPEN, }

    ## Display the record-id controlfield:
    out += \
     u"""   <controlfield tag="%(cf-tag-recid)s">%(recid)s</controlfield>\n""" \
     % { 'cf-tag-recid' : CFG_REFEXTRACT_CTRL_FIELD_RECID,
         'recid'        : encode_for_xml(recid),
       }

    ## Loop through all xml lines and add them to the output string:
    for line in xml_lines:
        out += line

    ## Now add the closing tag to the record:
    out += u"%(record-close)s\n" \
           % { 'record-close' : CFG_REFEXTRACT_XML_RECORD_CLOSE, }

    return out


def filter_processed_lines(out):
    """ apply filters to reference lines found - to remove junk"""
    lines = out.split('\n')

    new_out = '\n'.join([l for l in [rec.rstrip() for rec in lines] if l])

    if len(lines) != len(new_out):
        write_message("-----Filter results: unfiltered section line length" \
              "is %d and filtered length is %d\n" \
              %  (len(lines), len(new_out)), verbose=2)

    return new_out


def build_formatted_xml_author_affiliation_line(author_elements, first_author):
    """ Given a single line, of either:
    1. auth
    2. auth, aff
    3. aff
    Mark up into an xml form. No splitting heuristics are required, since all
    authors and associated affiliations will form single lines.
    @param author_elements: (list) The type of the item (affiliation or author)
    and the items content (the author or affiliation string)
    @param first_author: (boolean) Whether or not this is the first author-aff
    pair to mark up, for this document. This will influence the datafield tag used
    (100 or 700)
    @return: (string) The XML version of the passed in author-aff elements.
    """
    ## Begin the datafield element (no line marker)
    xml_line = start_auth_aff_datafield_element(first_author)

    line_elements = []
    citation_structure = []
    elements_processed = 0

    for element in author_elements:

        if element['type'] == "AUTH":
            ## Add the author subfield with the author text
            xml_line += """
      <subfield code="%(sf-code-ref-auth)s">%(content)s</subfield>""" \
                % {     'content'               : encode_for_xml(element['content']).strip('()'),
                        'sf-code-ref-auth'      : CFG_REFEXTRACT_AE_SUBFIELD_AUTHOR,
                 }
        elif element['type'] == "AFF":
            ## Add the affiliation subfield with the affiliation text
            xml_line += """
      <subfield code="%(sf-code-ref-auth)s">%(content)s</subfield>""" \
                % {     'content'               : encode_for_xml(element['content']).strip('()'),
                        'sf-code-ref-auth'      : CFG_REFEXTRACT_AE_SUBFIELD_AFFILIATION,
                 }
        line_elements.append(element)

    ## Close the ending datafield element
    xml_line += """
   </datafield>\n"""

    return xml_line


def start_auth_aff_datafield_element(first_author):
    """ Construct the first line of the XML datafield element,
        with the relevant datafield tag (depending on if it's
        the first author-aff pair or not).
        @param first_author: (boolean) Use the HEAD author tag
        or the TAIL author tag.
        @return: (string) The starting datafield line with the
        appropriate tag.
    """
    ## First author/affiliation? (use $100)
    if first_author:
        auth_tag = CFG_REFEXTRACT_AE_TAG_ID_HEAD_AUTHOR

    ## use $700
    else:
        auth_tag = CFG_REFEXTRACT_AE_TAG_ID_TAIL_AUTHOR

    new_datafield = """   <datafield tag="%(df-tag-auth)s" ind1=" " ind2=" ">""" \
    % { 'df-tag-auth'            : auth_tag,
    }

    return new_datafield
