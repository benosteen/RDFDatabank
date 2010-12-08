import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import is_embargoed

from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

from datetime import datetime, timedelta
from paste.fileapp import FileApp

import re

JAILBREAK = re.compile("[\/]*\.\.[\/]*")

import simplejson

log = logging.getLogger(__name__)

class SilosController(BaseController):
    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        c.ident = ident
        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
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
        
    def siloview(self, silo):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        if silo not in c.silos:
            abort(403, "Forbidden")
        
        c.silo_name = silo
        c.silo = ag.granary.get_rdf_silo(silo)
        
        c.embargos = {}
        for item in c.silo.list_items():
            c.embargos[item] = is_embargoed(c.silo, item)
        c.items = c.silo.list_items()
        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
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
                return simplejson.dumps(list(c.items))
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops nothing satisfies - return text/html            
        return render('/siloview.html')