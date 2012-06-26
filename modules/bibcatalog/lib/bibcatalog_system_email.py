# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Provide a "ticket" interface with Email.
This is a subclass of BibCatalogSystem
"""

import datetime
from time import mktime
import os
import invenio.webuser
from invenio.shellutils import run_shell_command, escape_shell_arg
from invenio.bibcatalog_system import BibCatalogSystem, get_bibcat_from_prefs
from invenio.mailutils import send_email
from invenio.config import CFG_BIBCATALOG_SYSTEM
    #CFG_BIBCATALOG_SYSTEM_TICKETS_EMAIL

class BibCatalogSystemEmail(BibCatalogSystem):

    #BIBCATALOG_RT_SERVER = "" #construct this by http://user:password@RT_URL

    def check_system(self, uid=None):
        """return an error string if there are problems"""
        pass

    
    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="", owner="", \
                      date_from="", date_until="", status="", priority="", queue=""):
        """Not implemented."""
        raise NotImplementedError




    def ticket_submit(self, uid=None, subject="", recordid=-1, text="", queue="", priority="", owner="", requestor=""):
        """creates a ticket. return true on success, otherwise false"""

        ticket_id = self._get_ticket_id()
        queueset = ""
        textset = ""
        priorityset = ""
        ownerset = ""
        subjectset = ""
        requestorset = ""
        if subject:
            subjectset = 'ticket #' + ticket_id + ' - ' + escape_shell_arg(subject)
        recidset = " CF-RecordID=" + escape_shell_arg(str(recordid))
        if priority:
            priorityset = " priority=" + escape_shell_arg(str(priority))
        if queue:
            queueset = " queue=" + escape_shell_arg(queue)
        if requestor:
            requestorset = " requestor=" + escape_shell_arg(requestor)
        if owner:
            #get the owner name from prefs
            ownerprefs = invenio.webuser.get_user_preferences(owner)
            if ownerprefs.has_key("bibcatalog_username"):
                owner = ownerprefs["bibcatalog_username"]
                ownerset = " owner=" + escape_shell_arg(owner)

        textset = escape_shell_arg(text)

        ok = False
        try:
            # from, to, subject, ??, text
            ok = send_email(fromaddr='eduadob@slac.stanford.edu', toaddr=CFG_BIBCATALOG_SYSTEM_TICKETS_EMAIL, subject=subjectset, header='Hi,\n', content=textset)
        except:
            #return False
            pass
        return ok


    def ticket_comment(self, uid, ticketid, comment):
        """comment on a given ticket. Returns 1 on success, 0 on failure"""
        pass


    def ticket_assign(self, uid, ticketid, to_user):
        """assign a ticket to an RT user. Returns 1 on success, 0 on failure"""
        pass


    def ticket_set_attribute(self, uid, ticketid, attribute, new_value):
        """change the ticket's attribute. Returns 1 on success, 0 on failure"""
        pass


    def ticket_get_attribute(self, uid, ticketid, attribute):
        pass


    def ticket_get_info(self, uid, ticketid, attributes = None):
        """return ticket info as a dictionary of pre-defined attribute names.
           Or just those listed in attrlist.
           Returns None on failure"""
        pass
    
    def _str_base(self, num, base, numerals = '0123456789abcdefghijklmnopqrstuvwxyz'):
        """ Convert number to base (2 to 36) """

        if base < 2 or base > len(numerals):
            raise ValueError("str_base: base must be between 2 and %i" % len(numerals))

        if num == 0:
            return '0'

        if num < 0:
            sign = '-'
            num = -num
        else:
            sign = ''

        result = ''
        while num:
            result = numerals[num % (base)] + result
            num //= base

        return sign + result


    def _get_ticket_id(self):
        """ Return timestamp in seconds since the Epoch converted to base36 """
     
        now =  datetime.datetime.now()    
        t = mktime(now.timetuple())+1e-6*now.microsecond
        
        t_str = str("%.6f" % t)
        t1, t2 = t_str.split('.')
        t_str = t1 + t2        
    
        #return base64.encodestring(t_str).strip()
        return self._str_base(int(t_str), 36)

