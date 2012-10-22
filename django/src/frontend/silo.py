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

# HTTP Method restriction
from django.views.decorators.http import require_http_methods, require_safe
from django.http import Http404, HttpResponse, HttpResponseForbidden

# Mako templating engine
from djangomako.shortcuts import render_to_response, render_to_string

import settings

import json

from utils.filestore import granary
from utils.solr_helper import getSiloModifiedDate

from utils.auth_entry import list_silos, get_datasets_count, authz, add_auth_info_to_context, list_user_permissions
from utils.conneg import MimeType as MT, parse as conneg_parse
from utils.bag import Context

import logging
log = logging.getLogger(__name__)

@require_http_methods(['GET', 'HEAD'])
def index(request):
    # logged in user
    c = Context()   # duck-typed context object for Mako
    c.ident = request.user
    add_auth_info_to_context(request, c)
    c.silos = list_silos()
   
    if settings.METADATA_EMBARGOED:
        #if not ident:
        #    abort(401, "Not Authorised")
        if request.user.is_authenticated():
            c.silos = authz(ident)
        else:
            return HttpResponseForbidden("Forbidden")

    c.silo_infos = {}
    for silo in c.silos:
        c.silo_infos[silo] = []
        state_info = granary.describe_silo(silo)
        if 'title' in state_info and state_info['title']:
            c.silo_infos[silo].append(state_info['title'])
        else:
            c.silo_infos[silo].append(silo)
        c.silo_infos[silo].append(get_datasets_count(silo))
        c.silo_infos[silo].append(getSiloModifiedDate(silo))
     
    # conneg return
    accept_list = None
    if request.META.has_key('HTTP_ACCEPT'):
        try:
            accept_list = conneg_parse(request.META['HTTP_ACCEPT'])
        except:
            accept_list= [MT("text", "html")]
    if not accept_list:
        accept_list= [MT("text", "html")]
    mimetype = accept_list.pop(0)
    while(mimetype):
        if str(mimetype).lower() in ["text/html", "text/xhtml"]:
            return render_to_response('list_of_silos.html', {'c':c})
        elif str(mimetype).lower() in ["text/plain", "application/json"]:
            response.content_type = 'application/json; charset="UTF-8"'
            response.status_int = 200
            response.status = "200 OK"
            return HttpResponse(json.dumps(c.silos), mimetype='application/json; charset="UTF-8"') 
        try:
            mimetype = accept_list.pop(0)
        except IndexError:
            mimetype = None

    return render_to_response('list_of_silos.html', {'c':c})
        
@require_http_methods(['GET', 'HEAD'])
def view(request, siloname):
    c = Context()   # duck-typed context object for Mako
    add_auth_info_to_context(request, c)
    if not granary.issilo(siloname):
        raise Http404

    ident = request.user
    c.ident = ident
    c.silo_name = siloname
    c.user_permissions = list_user_permissions(ident.username, siloname)
    c.editor = False
    if settings.METADATA_EMBARGOED:
        if request.user.is_authenticated():
            c.silos = authz(ident)
            if siloname in silos:
                c.editor = True
            else:
                return HttpResponseForbidden("Forbidden")
        else:
            return HttpResponseForbidden("Forbidden")
    else:
        c.silos = authz(ident)
        if siloname in c.silos:
            c.editor = True

    # FIXME: MAJOR issue - very specific 'if' here
    # TODO: Add a flag to the Silo model to mark whether a silo is
    # listable.
    if siloname in ['ww1archives', 'digitalbooks']:
        return HttpResponse("The silo %s contains too many data packages to list"%siloname, mimetype="text/plain")

    
    rdfsilo = granary.get_rdf_silo(siloname)
    state_info = granary.describe_silo(siloname)
    if 'title' in state_info and state_info['title']:
        c.title = state_info['title']
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
    if request.META.has_key('HTTP_ACCEPT'):
        try:
            accept_list = conneg_parse(request.META['HTTP_ACCEPT'])
        except:
            accept_list= [MT("text", "html")]
    if not accept_list:
        accept_list= [MT("text", "html")]
    mimetype = accept_list.pop(0)
    while(mimetype):
        if str(mimetype).lower() in ["text/html", "text/xhtml"]:
            return render_to_response('siloview.html', {'c':c})
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
    return render_to_response('siloview.html', {'c':c})
        
