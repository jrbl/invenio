
import invenio.webpage
import invenio.urlutils
import invenio.config
from invenio.webinterface_handler import WebInterfaceDirectory, wash_urlargd

class WebInterfaceEditAuthorPages(WebInterfaceDirectory):
    """Handle URLs is the /editauthors tree"""

    # List of valid URLs on this path
    _exports = ['', 'rec']

    def __init__(self):
        self.title = "BibEdit: Author Special Mode"

    def index(self, request, form):
        
        f = wash_urlargd(form, {
                'recID': (int, -1),
                })

        if f['recID'] != -1:
            return self.rec(request, f)

        text = "FIXME: This is a page for selecting the record to work with."
        return invenio.webpage.page(title = self.title,
                                    body  = text, 
                                    req   = request,)

    def rec(self, request, form):

        if not form.has_key('recID') or form['recID'] == -1:
            return self.index(request, {})
        else:
            text = "<p>Record ID: %s</p>" % form['recID']

        return invenio.webpage.page(title = self.title,
                                    body  = text, 
                                    req   = request,)

