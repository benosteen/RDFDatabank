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
import simplejson

from pylons import request, response, app_globals as ag
from pylons.controllers.util import abort
from pylons.decorators import rest

from rdfdatabank.lib.base import BaseController
from rdfdatabank.lib.utils import is_embargoed, serialisable_stat

log = logging.getLogger(__name__)

class StatesController(BaseController):
    @rest.restrict('GET')
    def siloview(self, silo):
        """Returns the state information of a silo. 
        Only authorized users with role 'admin' or 'manager' can view this information

The state information for a silo contains the following:
    Name of the silo (machine name, used in uris) - ans["silo"]
    Base URI for the silo - ans["uri_base"]
    Users who can access the silo (silo owners) - ans["owners"]
    Silo description - ans["description"]
    Title of the silo (human readable) - ans["title"]
    Disk allocation for the silo (in kB) - ans["disk_allocation"]
    List of datasets in the silo (ans["datasets"]) 
        with embargo information for each of the datasets (ans["datasets"]["dataset_name"]["embargo_info"])"""
    
        # Only authorized users can view state information.
        # Should this be restricted to admins and managers only, or shoud users too be able to see this information?
        # Going with restricting this information to admins and managers 
        if not ag.granary.issilo(silo):
            abort(404)

        ident = request.environ.get('repoze.who.identity')
        if not ident:
            abort(401, "Not Authorised")
        silos = ag.authz(ident)
        if silo not in silos:
            abort(403, "Forbidden")
        silos_admin = ag.authz(ident, permission='administrator')
        silos_manager = ag.authz(ident, permission='manager')
        #if not ident.get('role') in ["admin", "manager"]:
        if not (silo in silos_admin or silo in silos_manager):
            abort(403, "Forbidden. You should be an administrator or manager to view this information")

        rdfsilo = ag.granary.get_rdf_silo(silo)
        state_info = ag.granary.describe_silo(silo)
        state_info['silo'] = silo
        state_info['uri_base'] = ''
        if rdfsilo.state and rdfsilo.state['uri_base']:
            state_info['uri_base'] = rdfsilo.state['uri_base']
        items = {}
        for item in rdfsilo.list_items():
            #TODO: This is going to crash for silos with a large number fo datsets. get this information from SOLR or not give this info
            items[item] = {}
            items[item]['embargo_info'] = is_embargoed(rdfsilo, item)
        state_info['datasets'] = items

        # conneg return
        # Always return application/json
        response.content_type = 'application/json; charset="UTF-8"'
        response.status_int = 200
        response.status = "200 OK"
        return simplejson.dumps(state_info)

    @rest.restrict('GET')
    def datasetview(self, silo, id):       
        if not ag.granary.issilo(silo):
            abort(404)
        
        ident = request.environ.get('repoze.who.identity')

        if not ident:
            abort(401, "Not Authorised")

        silos = ag.authz(ident)
        if silo not in silos:
            abort(403, "Forbidden")
        silos_admin = ag.authz(ident, permission='administrator')
        silos_manager = ag.authz(ident, permission='manager')

        rdfsilo = ag.granary.get_rdf_silo(silo)       
        if not rdfsilo.exists(id):
            abort(404)

        item = rdfsilo.get_item(id)
        
        creator = None
        if item.manifest and item.manifest.state and 'metadata' in item.manifest.state and item.manifest.state['metadata'] and \
            'createdby' in item.manifest.state['metadata'] and item.manifest.state['metadata']['createdby']:
            creator = item.manifest.state['metadata']['createdby']
        #if not (ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]):
        if not (ident['repoze.who.userid'] == creator or silo in silos_admin or silo in silos_manager):
            abort(403, "Forbidden. You should be the creator or manager or administrator to view this information")
                    
        options = request.GET
        if 'version' in options and options['version']:
            if not options['version'] in item.manifest['versions']:
                abort(404)
            currentversion = str(item.currentversion)
            vnum = str(options['version'])
            if vnum and not vnum == currentversion:
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

