
import invenio.webpage
import invenio.template
from invenio.webinterface_handler import WebInterfaceDirectory, wash_urlargd

import invenio.editauthor_engine as engine

class WebInterfaceEditAuthorPages(WebInterfaceDirectory):
    """Handle URLs is the /editauthors tree"""

    # List of valid URLs on this path
    _exports = ['', 'rec']

    def __init__(self):
        self.title = "BibEdit: Author Special Mode"
        self.template = invenio.template.load('editauthor')
        self.columns_to_show = 10

    def index(self, request, form):
        
        f = wash_urlargd(form, {
                'recID': (int, -1),
                })

        if f['recID'] != -1:
            return self.rec(request, f)

        return invenio.webpage.page(title = self.title,
                                    body  = self.template.index(),
                                    req   = request,)

    def rec(self, request, form):

        if not form.has_key('recID') or form['recID'] == -1:
            return self.index(request, {})

        record_id = form['recID']

        author_list_gen = engine.auPairs(record_id)

        author_list = []
        place_list = []
        for group in author_list_gen:
            author_list.append(group)
            place_list.extend(group[1:])
        place_list = engine.flattenByCounts(place_list)

        text = self.template.record(record_id, author_list, place_list)

        return invenio.webpage.page(title = self.title,
                                    body  = text,
                                    req   = request,)

