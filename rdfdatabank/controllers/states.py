import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController
from rdfdatabank.lib.utils import is_embargoed, serialisable_stat

from datetime import datetime, timedelta
from paste.fileapp import FileApp

import re, os, shutil

JAILBREAK = re.compile("[\/]*\.\.[\/]*")

import simplejson

log = logging.getLogger(__name__)

class StatesController(BaseController):      
    def siloview(self, silo):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        if silo not in c.silos:
            abort(403, "Forbidden")

        c.silo = ag.granary.get_rdf_silo(silo)
        state_info = ag.granary.describe_silo(silo)
        c.embargos = {}
        for item in c.silo.list_items():
            c.embargos[item] = is_embargoed(c.silo, item)
        c.items = c.silo.list_items()
        # conneg return
        # Always return text/plain
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        items = {}
        for item_id in c.items:
            items[item_id] = {}
            items[item_id]['embargo_info'] = c.embargos[item_id]
        #state_info = {}
        state_info['silo'] = silo
        state_info['uri_base'] = ''
        if c.silo.state and c.silo.state['uri_base']:
            state_info['uri_base'] = c.silo.state['uri_base']
        state_info['datasets'] = items
        return simplejson.dumps(state_info)
 
    def datasetview(self, silo, id):       
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        if silo not in c.silos:
            abort(403, "Forbidden")

        c.silo_name = silo
        c.id = id
        c.silo = ag.granary.get_rdf_silo(silo)
        
        if not c.silo.exists(id):
            abort(404)

        c.item = c.silo.get_item(id)
                             
        c.parts = c.item.list_parts(detailed=True)
                    
        items = {}
        items['parts'] = {}
        for part in c.parts:
            items['parts'][part] = serialisable_stat(c.parts[part])
            if c.item.manifest:
                items['state'] = c.item.manifest.state
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        return simplejson.dumps(items)

    def datasetview_vnum(self, silo, id, vnum):       
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        if silo not in c.silos:
            abort(403, "Forbidden")

        c.silo_name = silo
        c.id = id
        c.silo = ag.granary.get_rdf_silo(silo)
        
        if not c.silo.exists(id):
            abort(404)

        c.item = c.silo.get_item(id)
              
        vnum = str(vnum)
        if not vnum in c.item.manifest['versions']:
            abort(404)
        c.item.set_version_cursor(vnum)                

        c.parts = c.item.list_parts(detailed=True)                    
        items = {}
        items['parts'] = {}
        for part in c.parts:
            items['parts'][part] = serialisable_stat(c.parts[part])
            if c.item.manifest:
                items['state'] = c.item.manifest.state
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        return simplejson.dumps(items)
