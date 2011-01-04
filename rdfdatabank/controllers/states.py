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
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if silo not in silos:
            abort(403, "Forbidden")

        rdfsilo = ag.granary.get_rdf_silo(silo)
        state_info = ag.granary.describe_silo(silo)
        state_info['silo'] = silo
        state_info['uri_base'] = ''
        if rdfsilo.state and rdfsilo.state['uri_base']:
            state_info['uri_base'] = rdfsilo.state['uri_base']
        items = {}
        for item in rdfsilo.list_items():
            items[item] = {}
            items[item]['embargo_info'] = is_embargoed(rdfsilo, item)
        state_info['datasets'] = items

        # conneg return
        # Always return application/json
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        return simplejson.dumps(state_info)

    def datasetview(self, silo, id):       
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if silo not in silos:
            abort(403, "Forbidden")

        rdfsilo = ag.granary.get_rdf_silo(silo)       
        if not rdfsilo.exists(id):
            abort(404)
        item = rdfsilo.get_item(id)
        parts = item.list_parts(detailed=True)
                    
        dataset = {}
        dataset['parts'] = {}
        for part in parts:
            dataset['parts'][part] = serialisable_stat(parts[part])
            if item.manifest:
                dataset['state'] = item.manifest.state

        # Always return application/json
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        return simplejson.dumps(dataset)

    def datasetview_vnum(self, silo, id, vnum):       
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if silo not in silos:
            abort(403, "Forbidden")

        rdfsilo = ag.granary.get_rdf_silo(silo)
        
        if not rdfsilo.exists(id):
            abort(404)

        item = rdfsilo.get_item(id)
        vnum = str(vnum)
        if not vnum in item.manifest['versions']:
            abort(404)
        item.set_version_cursor(vnum)                

        parts = item.list_parts(detailed=True)                    

        dataset = {}
        dataset['parts'] = {}
        for part in parts:
            dataset['parts'][part] = serialisable_stat(parts[part])
            if item.manifest:
                dataset['state'] = item.manifest.state

        # Always return application/json
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        return simplejson.dumps(dataset)
