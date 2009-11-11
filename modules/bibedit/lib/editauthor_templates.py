import invenio.config

class Template:

    def __init__(self):
        """Establish some variables we can use throughout"""
        self.javascript = ['jquery.min.js']

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

    def record(self, record_id, auth_inst_pairs, allplaces):
        a_width = len(allplaces) 
        t = self.setup_scripts()
        t += '<table>\n<tr><th>name</th><th>affiliations</th>'
        for place in allplaces:
            t += "<th>%s</th>" % place
        t += '</tr>\n'
        for author, institution in auth_inst_pairs:
            t += "<tr><td>%s</td><td>%s</td>" % (author, institution)
            t += "<td></td>" * a_width
            t += "<tr>\n"
        t += '</table>\n'
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

