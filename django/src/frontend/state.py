# HTTP Method restriction
from django.views.decorators.http import require_http_methods, require_safe
from django.http import Http404, HttpResponse, HttpResponseForbidden

# Mako templating engine
from djangomako.shortcuts import render_to_response, render_to_string

import settings

import json

from utils.filestore import granary
from utils.solr_helper import getSiloModifiedDate
from utils.redis_helper import r, b
from utils.misc import is_embargoed

from utils.auth_entry import get_datasets_count, get_datasets, authz, add_auth_info_to_context
from utils.conneg import MimeType as MT, parse as conneg_parse
from utils.bag import Context

import logging
log = logging.getLogger(__name__)

@require_http_methods(['GET', 'HEAD'])
def silo_view(request, siloname):
    # Only authorized users can view state information.
    if not granary.issilo(siloname):
        raise Http404

    ident = request.user
    if not ident.is_authenticated():
        return HttpResponseForbidden("Not Authorised")
        
    silos = authz(ident)
    if siloname not in silos:
        return HttpResponseForbidden("Forbidden")
    
    silos_admin = authz(ident, permission='administrator')
    silos_manager = authz(ident, permission='manager')
    #if not ident.get('role') in ["admin", "manager"]:
    if not (siloname in silos_admin or siloname in silos_manager):
        return HttpResponseForbidden(403, "Forbidden")

    options = request.GET
    start = 0
    if 'start' in options and options['start']:
        try:
            start = int(options['start'])
        except:
            start = 0
    rows = 1000
    if 'rows' in options and options['rows']:
        try:
            rows = int(options['rows'])
        except:
            rows = 1000

    rdfsilo = granary.get_rdf_silo(siloname)
    state_info = granary.describe_silo(siloname)
    state_info['silo'] = siloname
    state_info['uri_base'] = ''
    if rdfsilo.state and rdfsilo.state['uri_base']:
        state_info['uri_base'] = rdfsilo.state['uri_base']
    state_info['number of data packages'] = get_datasets_count(siloname)
    state_info['params'] = {'start':start, 'rows':rows}
    items = {}
    #for item in rdfsilo.list_items():
    for item in get_datasets(siloname, start=start, rows=rows):
        items[item] = {}
        try:
            items[item]['embargo_info'] = is_embargoed(rdfsilo, item)
        except:
            pass
    state_info['datasets'] = items
    return HttpResponse(json.dumps(state_info), mimetype='application/json; charset="UTF-8"')


@require_http_methods(['GET', 'HEAD'])
def dataset_view(self, siloname, id):
    # Only authorized users can view state information.
    if not granary.issilo(siloname):
        raise Http404
        
    ident = request.user
    if not ident.is_authenticated():
        return HttpResponseForbidden("Not Authorised")
        
    silos = authz(ident)
    if siloname not in silos:
        return HttpResponseForbidden("Forbidden")
    
    silos_admin = authz(ident, permission='administrator')
    silos_manager = authz(ident, permission='manager')
    
    rdfsilo = granary.get_rdf_silo(siloname)
    if not rdfsilo.exists(id):
        raise Http404

    item = rdfsilo.get_item(id)
        
    creator = None
    
    if item.manifest and item.manifest.state and 'metadata' in item.manifest.state and item.manifest.state['metadata'] and \
            'createdby' in item.manifest.state['metadata'] and item.manifest.state['metadata']['createdby']:
        creator = item.manifest.state['metadata']['createdby']
    
    if not (ident.username == creator or siloname in silos_admin or siloname in silos_manager):
        return HttpResponseForbidden("Forbidden")

    options = request.GET
    if 'version' in options and options['version']:
        if not options['version'] in item.manifest['versions']:
            raise Http404
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
    return HttpResponse(json.dumps(dataset), mimetype='application/json; charset="UTF-8"')

