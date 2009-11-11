
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

        authors = engine.recid2names(record_id)
        allplaces = []
        auth_inst_pairs = []
        for author in authors:
            thisauth = False
            for id, name, inst in engine.name2affils(author, record_id):
                if inst != None:
                    if not thisauth:
                        thisauth = True
                        auth_inst_pairs.append( (name, inst) )
                    allplaces.append( inst )
        allplaces = engine.flattenByCounts(allplaces)[:self.columns_to_show]

        text = self.template.record(record_id, auth_inst_pairs, allplaces)

        return invenio.webpage.page(title = self.title,
                                    body  = text,
                                    req   = request,)

