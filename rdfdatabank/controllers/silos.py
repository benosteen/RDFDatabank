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
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        c.ident = ident
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
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        if silo not in c.silos:
            abort(403, "Forbidden")
        
        c.silo_name = silo
        rdfsilo = ag.granary.get_rdf_silo(silo)       
        c.embargos = {}
        c.items = []
        for item in rdfsilo.list_items():
            c.embargos[item] = None
            c.embargos[item] = is_embargoed(rdfsilo, item)
            c.items.append(item)

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
