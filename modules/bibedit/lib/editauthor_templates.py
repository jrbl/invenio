import invenio.config

import simplejson            # FIXME: remember to be defensive
import math                  # floor()


class Template:
    """Tell Invenio how to produce output for our various URLs"""

    def __init__(self):
        """Establish some variables we can use throughout"""
        self.javascript = [ # prerequisites for hotkeys, autocomplete
                           #'jquery-1.4.4.js', 
                           # FIXME we should be using a locally cached version of jquery-1.4.4... shouldn't we?
                           'http://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js',
                           # FIXME we should be using locally cached version of jquery-ui libs... shouldn't we?
                           'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.11/jquery-ui.min.js',
                           # FIXME we should be using locally cached version of jquery hotkeys... but this version!
                           'https://github.com/jeresig/jquery.hotkeys/raw/master/jquery.hotkeys.js',
                           'editauthor.js'
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

    def record(self, record_id, author_list, affiliations, offset=0, per_page=100, title='', valid_affils = []):
        """Template for individual record display/edit"""
        return """%(script_parts)s
<script type="text/javascript">
    shared_data["authors"] = %(author_list_json)s;
    shared_data["affiliations"] = %(affiliation_list_json)s;
    shared_data["paging"] = {pages: 1, offset: %(offset)s, rows: %(per_page)s, };
    shared_data["headline"] = {recid: "%(record_id)s", title: "%(paper_title)s", };
    //shared_data["valid_affils"] = %(valid_affils_list_json)s;
</script>
<div id="asm_form" title="Please wait while loading...">
    <form method="post" action="%(site_URL)s/editauthors/process">
        <div id="paging_navigation" style="display: none;"></div>
        <table id="asm_uitable" bgcolor="#ff2200">     <!-- Red means a javascript parse error -->
            <thead id="TableHeaders">
                <td>
                If you can read this message, then something went wrong during
                document load.  The most likely explanation is that your site
                hasn't installed the jQuery plugins.
                </td>
            </thead>
            <tbody id="TableContents">
            </tbody>
        </table>
        <span id="formbuttons">
            <input name="recID" type="hidden" value="%(record_id)s">
            <!-- Submit button is unhidden by jQuery code -->
            <input id="submit_button" name="submit_button" type="submit" value="Submit" class="control_button" style="display: none;">
        </span>
    </form>
</div>
""" % {
       'script_parts'           : self.setup_scripts(),
       'author_list_json'       : simplejson.dumps(author_list),
       'affiliation_list_json'  : simplejson.dumps(affiliations),
       'valid_affils_list_json' : simplejson.dumps(valid_affils),
       'site_URL'               : invenio.config.CFG_SITE_URL,
       'record_id'              : str(record_id),
       'per_page'               : str(per_page),
       'offset'                 : str(offset),
       'paper_title'            : title,
      }
              
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
