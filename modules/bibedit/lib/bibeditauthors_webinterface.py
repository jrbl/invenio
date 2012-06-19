import invenio.webpage
import invenio.template
from invenio.config import CFG_SITE_URL, CFG_SITE_RECORD
from invenio.webinterface_handler import WebInterfaceDirectory, wash_urlargd

import invenio.bibeditauthors_engine as engine
import invenio.bibedit_utils as utils
import invenio.webuser as webuser
import invenio.access_control_engine as webuser_access
import invenio.bibtask as bibtask
import invenio.bibknowledge as bibknowledge
from invenio.jsonutils import json, json_unicode_to_utf8, CFG_JSON_AVAILABLE


class WebInterfaceEditAuthorPages(WebInterfaceDirectory):
    """Handle URLs is the record/editauthors tree"""

    # List of valid URLs on this path
    _exports = ['', '/', 'rec', 'checkAffil', 'process']

    def __init__(self):
        self.title = "Author Special Mode" 
        self.template = invenio.template.load('bibeditauthors')
        self.columns_to_show = 10

    def index(self, request, form):

        permission = check_request_allowed(request)
        if permission != True:
            return permission

        f = wash_urlargd(form, {
                'recid':   (int, -1),
                'offset':  (int, 0),
                'perPage': (int, 30),
                })

        if f['recid'] != -1:
            return self.rec(request, f)

        return invenio.webpage.page(title = self.title,
                                    body = self.template.index(),
                                    req = request)

    def rec(self, request, form):

        permission = check_request_allowed(request)
        if permission != True:
            return permission

        if not 'recid' in form or form['recid'] == -1:
            return self.index(request, {})

        record_id = form['recid']
        offset    = form['offset']
        per_page  = form['perPage']

        author_list_gen = engine.auPairs(record_id)

        author_list = []
        place_list = []
        for group in author_list_gen:
            author_list.append(group)
            place_list.extend(group[1:])
        place_list = engine.flattenByCounts(place_list)

        text = self.template.record(record_id,
                                    author_list,
                                    place_list,
                                    offset,
                                    per_page,
                                    engine.get_title(record_id),
                                    )

        return invenio.webpage.page(title = self.title,
                                    body = text,
                                    req = request)

    def process(self, request, form):

        permission = check_request_allowed(request)
        if permission != True:
            return permission

        def get_washer(form):
            washer = {}
            for key in form:
                tag = key[0:5]
                if (tag == "autho") or (tag == "insts") or (tag == "recid"):
                    washer[key] = (str, '')
            return washer

        form_data = wash_urlargd(form, get_washer(form))
            # clean up unicode entitites
        form_data = json_unicode_to_utf8(form_data)
            # minus 'ln' key and 'recid' key, / paired items
        form_length = (len(form_data) - 2) / 2

        recid = form_data.get('recid')
        if not recid or not form_data.get('autho0'):
            return self._broken_record_error(form_data, request)

        new_doc = '<?xml version="1.0" encoding="UTF-8"?>\n'
        new_doc += '<collection xmlns="http://www.loc.gov/MARC21/slim">\n'
        new_doc += "<record>\n  <controlfield tag=\"001\">"
        new_doc += "%s</controlfield>\n" % recid
        new_doc += "  <datafield tag=\"100\" ind1=\" \" ind2=\" \">\n"
        new_doc += "    <subfield code=\"a\">"
        new_doc += "%s</subfield>\n" % form_data['autho0']
        for sub in form_data.get('insts0', '').split(';'):
            sub = sub.strip()
            if sub != '':
                new_doc += "    <subfield code=\"u\">%s</subfield>\n" % sub
        new_doc += "  </datafield>\n"
        for i in range(1, form_length):
            new_doc += "  <datafield tag=\"700\" ind1=\" \" ind2=\" \">\n"
            new_doc += "    <subfield code=\"a\">"
            new_doc += "%s</subfield>\n" % form_data.get('autho%s'%i, '')
            for sub in form_data.get('insts%s'%i, '').split(';'):
                sub = sub.strip()
                if sub != '':
                    new_doc += "    <subfield code=\"u\">%s</subfield>\n" % sub
            new_doc += "  </datafield>\n"
        new_doc += "</record>\n</collection>"

            # Don't use utils.save_xml_record because record isn't complete
        newdoc_filename = utils._get_file_path(recid, webuser.getUid(request))
        newdoc_file = open(newdoc_filename, 'w')
        newdoc_file.write(new_doc)
        newdoc_file.close()
        bibtask.task_low_level_submission('bibupload', 'bibedit', '-P', '5', '-c', newdoc_filename)

        ret_title = "editauthors: Record %s submitted" % recid
        ret_body = "The updated author list has been submitted to the job queue.  "
        ret_body += "Results are typically visible in five to ten minutes.  "
        ret_body += "<a href='%s'>Click here to check.</a>" % (CFG_SITE_URL + '/' + CFG_SITE_RECORD + '/' + recid)
        return invenio.webpage.page(title = ret_title,
                                    body = ret_body,
                                    req = request)

    def _debugPrint(self, form):
        t = ''
        import pprint
        import cStringIO
        buf = cStringIO.StringIO()
        pp = pprint.PrettyPrinter(stream=buf, indent=4, width=120)
        t = "<pre>\n"
        pp.pprint(form)
        t += buf.getvalue()
        t += "\n</pre>\n"
        return t

    def _broken_record_error(self, form_data, req):
        """Freak out about missing or incorrect recid or 1st author info"""
        return_body = "<p>Warning: No data will be saved.  Something went wrong "
        return_body += "talking to the database or to your web browser, and we "
        return_body += "got a record to process which was missing either the record "
        return_body += "id number, which should be impossible, or was missing its "
        return_body += "first author designation.</p>"
        return_body += "<p>If you are sure that your first author was good and "
        return_body += "the website has been behaving well up until now, please "
        return_body += "report this problem to your site administrators immediately. "
        return_body += "They will benefit if you give them the time that the error "
        return_body += "occurred, the URL in the bar above, and everything on this "
        return_body += "page. On most browsers you can select everything on this "
        return_body += "page for pasting into an email by pressing Ctrl-A to "
        return_body += "select everything, and then Ctrl-C to Copy it.  In your "
        return_body += "email program, Ctrl-V usually pastes.</p>"
        return_body += "<p>If you're not certain you did the right thing, please "
        return_body += "use your browser's back button to make sure everything is "
        return_body += "right.</p>"
        return_body += "<p>Potentially useful debugging information follows:</p> "
        return_body += self._debugPrint(form_data)
        return_body += self._debugPrint(req)
        return invenio.webpage.page(title = "BibEditAuthors Warning: No data will be saved", 
                                    body = return_body, req = req)

    def __call__(self, request, form):
        return self.index(request, form)


def check_request_allowed(request):
    """Is this request allowed to this user?  Return True or a failure page."""
    code, message = webuser_access.acc_authorize_action(request, 'runbibedit')
    if code != 0:
        return webuser.page_not_authorized(req = request,
                                           referer = '/record/editauthors',
                                           text = message)
    else:
        return True
