import invenio.config

import simplejson            # FIXME: remember to be defensive

class Template:

    def __init__(self):
        """Establish some variables we can use throughout"""
        self.javascript = ['jquery.min.js', 'editauthor.js']

    def setup_scripts(self):
        """Output a bunch of <script> bits."""
        t = ''
        for script in self.javascript:
            t += ("<script type=\"text/javascript\" src=\"%s/js/%s\">" % 
                                       (invenio.config.CFG_SITE_URL, script))
            t += "</script>\n" 
        return t

    def index(self):
        """structure of the index page, with form elements etc."""
        t = self.setup_scripts()
        t += self.tPara("This page is a placeholder for where you can select" +
                        " the records to work with.", id='FIXME_index')
        return t

    def record(self, record_id, author_list, affiliations):
        t = self.setup_scripts()
        t += '<script type="text/javascript">\nshared_data["authors"] =' + simplejson.dumps(author_list) + ';\n'
        t += 'shared_data["affiliations"] = ' + simplejson.dumps(affiliations) + ';\n</script>\n'
        t += '<form method="post" action="'+invenio.config.CFG_SITE_URL+'/editauthors/process">\n'
        t += '<table bgcolor="#ff2200">\n  <thead id="TableHeaders">\n  </thead>\n'
        t += '  <tbody id="TableContents">\n  </tbody>\n </table>\n<span id="formbuttons"><input name="recID" type="hidden" value="' + str(record_id)
        t += '"<input id="submit_button" type=submit value="Submit" class="control_button">'
        t += '</span></form>\n'

        return t

    def tPara(self, s, indent=0, id=''):
        t = ' '*indent + "<p id=%s>\n" % id
        t += ' '*indent + "%s\n" % s
        t += ' '*indent + '</p>\n'
        return t

    def tList(self, l, indent=0, tagas=''):
        """Output an HTML list"""
        t = ' '*indent + "<ul class=\"%s\">\n" % id
        for i in l:
            t += ' '*indent + " <li>%s</li>\n" % str(i)
        t += ' '*indent + '</ul>\n'
        return t
