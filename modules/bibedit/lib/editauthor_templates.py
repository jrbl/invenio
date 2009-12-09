import invenio.config

import simplejson            # FIXME: remember to be defensive

class Template:
    """Tell Invenio how to produce output for our various URLs"""

    def __init__(self):
        """Establish some variables we can use throughout"""
        self.javascript = ['jquery.min.js', 'jquery.hotkeys.min.js', 
                           'editauthor.js']

    def setup_scripts(self):
        """Output a bunch of <script> bits."""
        ostr = ''
        for script in self.javascript:
            ostr += ("<script type=\"text/javascript\" src=\"%s/js/%s\">" % 
                                       (invenio.config.CFG_SITE_URL, script))
            ostr += "</script>\n" 
        return ostr

    def index(self):
        """structure of the index page, with form elements etc."""
        ostr = self.setup_scripts()
        ostr += self.tPara("This page is a placeholder for where you can select" +
                        " the records to work with.", id='FIXME_index')
        return ostr

    def record(self, record_id, author_list, affiliations, valid_affils = []):
        """Template for individual record display/edit"""
        ostr = self.setup_scripts()
        ostr += '<script type="text/javascript">\n'
        ostr += 'shared_data["authors"] =' + simplejson.dumps(author_list)
        ostr += ';\nshared_data["affiliations"] = ' + simplejson.dumps(affiliations) 
        ostr += ';\nshared_data["valid_affils"] = ' + simplejson.dumps(valid_affils)
        ostr += ';\n</script>\n<form method="post" action="'
        ostr += invenio.config.CFG_SITE_URL+'/editauthors/process">\n'
        ostr += '<table bgcolor="#ff2200">\n  <thead id="TableHeaders">\n'
        ostr += '  </thead>\n  <tbody id="TableContents">\n  </tbody>\n'
        ostr += ' </table>\n<span id="formbuttons">'
        ostr += '<input name="recID" type="hidden" value="' + str(record_id)
        ostr += '"<input id="submit_button" type=submit value="Submit"'
        ostr += 'class="control_button"></span></form>\n'

        return ostr

    def tPara(self, instr, indent=0, tagas=''):
        """Output an HTML paragraph"""
        ostr = ' '*indent + "<p id=%s>\n" % tagas
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
