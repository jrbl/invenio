
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

        authors = engine.recid2names(record_id)
        affils = {}
        for author in authors:
            for id, name, inst in engine.name2affils(author, record_id):
                if affil != None:
                    if not affils.has_key(author):
                        affils[author] = [inst]
                    else:
                        affils[author].append(inst)

        text = self.template.record(record_id, affils)

        return invenio.webpage.page(title = self.title,
                                    body  = text,
                                    req   = request,)

