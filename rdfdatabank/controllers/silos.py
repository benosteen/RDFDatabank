# -*- coding: utf-8 -*-
"""
Copyright (c) 2012 University of Oxford

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import logging
from datetime import datetime, timedelta
import re
import simplejson

from pylons import request, response, session, tmpl_context as c, app_globals as ag, url
from pylons.controllers.util import abort
from pylons.decorators import rest
from paste.fileapp import FileApp

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import is_embargoed
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

JAILBREAK = re.compile("[\/]*\.\.[\/]*")

log = logging.getLogger(__name__)

class SilosController(BaseController):
    @rest.restrict('GET')
    def index(self):
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = granary_list
        if ag.metadata_embargoed:
            if not ident:
                abort(401, "Not Authorised")
            c.silos = ag.authz(granary_list, ident)

        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            try:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]
        mimetype = accept_list.pop(0)
        while(mimetype):
            if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                return render('/list_of_silos.html')
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                response.content_type = 'application/json; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                list_of_silos = []
                for silo_id in c.silos:
                    list_of_silos.append(silo_id)
                return simplejson.dumps(list_of_silos)
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops nothing satisfies - return text/html            
        return render('/list_of_silos.html')
        
    @rest.restrict('GET')
    def siloview(self, silo):
        if not ag.granary.issilo(silo):
            abort(404)
            
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silo_name = silo
        c.editor = False
        if ag.metadata_embargoed:
            if not ident:
                abort(401, "Not Authorised")
            silos = ag.authz(granary_list, ident)
            if silo not in silos:
                abort(403, "Forbidden")
            c.editor = True
        elif ident:
            silos = ag.authz(granary_list, ident)
            if silo in silos:
                c.editor = True
        
        rdfsilo = ag.granary.get_rdf_silo(silo)       
        c.embargos = {}
        c.items = []
        for item in rdfsilo.list_items():
            c.embargos[item] = None
            try:
                c.embargos[item] = is_embargoed(rdfsilo, item)
            except:
                pass
            c.items.append(item)
            #c.embargos[item] = ()

        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            try:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]
        mimetype = accept_list.pop(0)
        while(mimetype):
            if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                return render('/siloview.html')
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                response.content_type = 'application/json; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return simplejson.dumps(c.embargos)
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops nothing satisfies - return text/html            
        return render('/siloview.html')
