import invenio.config
from invenio.jsonutils import json, CFG_JSON_AVAILABLE

import math                  # floor()


class Template:
    """Tell Invenio how to produce output for our various URLs"""

    def __init__(self):
        """Establish some variables we can use throughout"""
        self.javascript = [ # prerequisites for hotkeys, autocomplete
                           'jquery-1.4.4.js', 
                           # FIXME we should be using a locally cached version of jquery-1.4.4... shouldn't we?
                           #'http://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js',
                           # FIXME we should be using locally cached version of jquery-ui libs... shouldn't we?
                           #'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.11/jquery-ui.min.js',
                           # we include this in the Makefile.am at root, but maybe that wasn't a good idea?
                           'jquery-ui.min.js', 
                           # FIXME we should be using locally cached version of jquery hotkeys... but this version!
                           #'https://github.com/jeresig/jquery.hotkeys/raw/master/jquery.hotkeys.js',
                           # we include this in the root Makefile.am too, but it's also not clear if it's a good idea
                           'jquery.hotkeys.js',
                           'bibeditauthors.js'
                          ]

    def setup_scripts(self):
        """Output a bunch of <script> bits."""
        ostr = ''
        for script in self.javascript:
            if script.startswith('http'):
                ostr += ("<script type=\"text/javascript\" src=\"%s\">" % script)
            else:
                ostr += ("<script type=\"text/javascript\" src=\"%s/js/%s\">" %
                                           (invenio.config.CFG_SITE_URL, script))
            ostr += "</script>\n"
        return ostr

    def index(self):
        """structure of the index page, with form elements etc."""
        ostr = self.setup_scripts()
        ostr += self.tPara("This page is a placeholder for selecting " +
                           "the records to work with.", tagas='FIXME_index')
        return ostr

    def lockedrecord(self):
        """Complain that the record is locked by some other user or possibly bibsched is running."""
        ostr = self.tPara("Record is locked. It could be some other user is editing it, or that it's running through bibsched." +
                           "Please ask your local Invenio developer to make this error message more helpful.", tagas='FIXME_lockedrecord')
        return ostr

    def record(self, record_id, author_list, affiliations, offset=0, per_page=30, title='', valid_affils = []):
        """Template for individual record display/edit"""
        if CFG_JSON_AVAILABLE:
            return self._record_normal_display(record_id, author_list, 
                                               affiliations, offset, per_page, 
                                               title, valid_affils)
        else:
            return self._simplejson_error()

    def _record_normal_display(self, record_id, author_list, affiliations, offset, per_page, title, valid_affils):
        return """%(script_parts)s
<script type="text/javascript">
    shared_data["authors"] = %(author_list_json)s;
    shared_data["affiliations"] = %(affiliation_list_json)s;
    shared_data["paging"] = {pages: 1, offset: %(offset)s, rows: %(per_page)s, };
    shared_data["headline"] = {recid: "%(record_id)s", title: "%(paper_title)s", };
    //shared_data["valid_affils"] = %(valid_affils_list_json)s;
</script>
<div id="editauthors_form" title="Please wait while loading...">
    <form method="post" action="%(site_URL)s/record/editauthors/process">
        <div id="paging_navigation" style="display: none;"></div>
        <div id="NonTableHeaders"></div>
        <table id="asm_uitable" bgcolor="#ff2200">     <!-- Red means a javascript parse error -->
            <tbody id="TableContents">
            </tbody>
        </table>
        <span id="formbuttons">
            <input name="recid" type="hidden" value="%(record_id)s">
            <!-- Submit button is unhidden by jQuery code -->
            <input id="submit_button" name="submit_button" type="submit" value="Submit" class="formbutton" style="display: none;">
        </span>
    </form>
</div>
""" % {
       'script_parts'           : self.setup_scripts(),
       'author_list_json'       : json.dumps(author_list),
       'affiliation_list_json'  : json.dumps(affiliations),
       'valid_affils_list_json' : json.dumps(valid_affils),
       'site_URL'               : invenio.config.CFG_SITE_URL,
       'record_id'              : str(record_id),
       'per_page'               : str(per_page),
       'offset'                 : str(offset),
       'paper_title'            : title,
      }

    def _simplejson_error(self):
        return """
<div id="editauthors_form" title="Author editing missing dependency">
    <p class="warningred">
        Please notify your system administrator that the <i>simplejson</i> 
        module is not usably installed, and that without it, bibeditauthors 
        is unable to properly function.
    </p>
</div>"""

              
    def tPara(self, instr, indent=0, tagas=''):
        """Output an HTML paragraph"""
        ostr  = ' '*indent + "<p id=%s>\n" % tagas
        ostr += ' '*indent + "%s\n" % instr
        ostr += ' '*indent + '</p>\n'
        return ostr

    def tList(self, lst, indent=0, tagas=''):
        """Output an HTML list"""
        ostr = ' '*indent + "<ul class=\"%s\">\n" % tagas
        for item in lst:
            ostr += ' '*indent + " <li>%s</li>\n" % str(item)
        ostr += ' '*indent + '</ul>\n'
        return ostr