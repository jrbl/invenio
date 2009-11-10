import invenio.editauthor_engine as engine

class Template:

    def index(self):
        """structure of the index page, with form elements etc."""
        t = "This page is a placeholder for where you can select "
        t += "the records to work with."
        return self.tPara(t, id='FIXME_index')

    def record(self, record_id, authors, affiliations):
        a_width = len(affiliations) 
        t = '<table>\n<tr><th>name</th>'
        for aff in affiliations:
            t += "<th>%s</th>" % aff
        t += '</tr>\n'
        for author in authors:
            t += "<tr><td>%s</td>" % author
            t += "<td> </td>" * a_width
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

