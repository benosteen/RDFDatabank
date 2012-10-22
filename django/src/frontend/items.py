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

from django.core.urlresolvers import reverse

# Mako templating engine
from djangomako.shortcuts import render_to_response, render_to_string

import settings

import json

from utils.filestore import granary
from utils.redis_helper import b
from utils.file_unpack import check_file_mimetype, BadZipfile, get_zipfiles_in_dataset, unpack_zip_item, read_zipfile

from utils.misc import create_new, allowable_id2

from utils.auth_entry import list_silos, get_datasets_count, authz, add_auth_info_to_context, list_user_permissions
from utils.conneg import MimeType as MT, parse as conneg_parse
from utils.bag import Context

import logging
log = logging.getLogger(__name__)

def silo_view(request, siloname):
    return HttpResponseForbidden("Forbidden")

def dataset_view(request, siloname, id):
    if not granary.issilo(siloname):
        raise Http404
    
    rdfsilo = granary.get_rdf_silo(siloname)
    if not rdfsilo.exists(id):
        raise Http404
            
    c = Context()
    silo = siloname
    #tmpl_context variables needed: c.silo_name, c.zipfiles, c.ident, c.id, c.path
    c.silo_name = siloname
    c.id = id
    ident = request.user
    c.ident = ident.username
    dataset = rdfsilo.get_item(id)

    creator = None
    if dataset.manifest and dataset.manifest.state and 'metadata' in dataset.manifest.state and dataset.manifest.state['metadata'] and \
                                   'createdby' in dataset.manifest.state['metadata'] and dataset.manifest.state['metadata']['createdby']:
        creator = dataset.manifest.state['metadata']['createdby']

    http_method = request.method
        
    if http_method == "GET":
        c.editor = False
        if settings.METADATA_EMBARGOED:
            if not ident:
                return HttpResponse("Not Authorised", status=401)
            silos = authz(ident)
            if silo not in silos:
                return HttpResponseForbidden("Forbidden")
            silos_admin = authz(ident, permission='administrator')
            silos_manager = authz(ident, permission='manager')
            if c.ident == creator or silo in silos_admin or silo in silos_manager:
                c.editor = True
        elif ident:
            silos = authz(ident)
            if silo in silos:
                silos_admin = authz(ident, permission='administrator')
                silos_manager = authz(ident, permission='manager')
                if ident['repoze.who.userid'] == creator or silo in silos_admin or silo in silos_manager:
                    c.editor = True
    else:
        #identity management of item 
        if not ident:
            return HttpResponse("Not Authorised", status=401)
        silos = authz(ident)      
        if silo not in silos:
            return HttpResponseForbidden("Forbidden")
        silos_admin = authz(ident, permission='administrator')
        silos_manager = authz(ident, permission='manager')
        if not (c.ident == creator or silo in silos_admin or silo in silos_manager):
            return HttpResponseForbidden("Forbidden")

    if http_method == "GET":
        c.zipfiles = get_zipfiles_in_dataset(dataset)
        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.META:
            try:
                accept_list = conneg_parse(request.META['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]
        mimetype = accept_list.pop(0)
        while(mimetype):
            if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                return render_to_response("/list_of_zipfiles.html", {'c':c,})
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                return HttpResponse(json.dumps(list(c.zipfiles.keys())), 
                                    mimetype = 'application/json; charset="UTF-8"')
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops nothing satisfies - return text/html            
        return render_to_response("/list_of_zipfiles.html", {'c':c,})
    elif http_method == "POST":
        params = request.POST
        if not (params.has_key("filename") and params['filename']):
            return HttpResponse("You must supply a filename to unpack", status=400)

        item_real_filepath = dataset.to_dirpath()
        target_filepath = "%s/%s"%(item_real_filepath, params['filename'])
        if not os.path.isfile(target_filepath):
            return HttpResponse("File to unpack not found", status=404)
        if not check_file_mimetype(target_filepath, 'application/zip'):
            return HttpResponse("File is not of type application/zip", status=415)

        if params.has_key("id") and params['id']:
            target_dataset_name = params['id']
        else:
            target_dataset_name = id

        #step 1: Create / initialize target dataset 
        if not rdfsilo.exists(target_dataset_name):
            if not allowable_id2(target_dataset_name):
                return HttpResponse("Data package name can contain only the following characters - %s and has to be more than 1 character"%ag.naming_rule_humanized,
                                    status=400,
                                    mimetype="text/plain")
            target_dataset = create_new(rdfsilo, target_dataset_name, c.ident)
            hr = HttpResponse("Created",
                                status=201,
                                mimetype="text/plain")
            hr["Content-Location"] = reverse("dataset_view", kwargs={'siloname': siloname, 'id': target_dataset_name})
        else:
            hr = HttpResponse("204 Updated",
                                status=204,
                                mimetype="text/plain")
            target_dataset = rdfsilo.get_item(target_dataset_name)

        #step 2: Unpack zip item 
            
        try:
            unpack_zip_item(target_dataset, dataset, params['filename'], rdfsilo, c.ident)
        except BadZipfile:
            return HttpResponse("BadZipfile: Couldn't unpack zipfile", status=400, mimetype="text/plain")

        # FIXME: err.. wat is this?!
        target_dataset.sync()
        target_dataset.sync()
        target_dataset.sync()

        if hr.status == 201:
            try:
                b.creation(silo, id, ident=c.ident)
            except:
                pass
        else:
            try:
                b.change(silo, id, ident=c.ident)
            except:
                pass

        # conneg return
        accept_list = None
        if 'HTTP_ACCEPT' in request.META:
            try:
                accept_list = conneg_parse(request.META['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]
        mimetype = accept_list.pop(0)
        while(mimetype):
            if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                return redirect(reverse("dataset_view", kwargs={'silo': silo, 'id': id}))
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                hr.mimetype = "text/plain"
                return hr
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        # Whoops - nothing satisfies - return text/plain
        hr.mimetype = "text/plain"
        return hr
    
def item_view(request, siloname, id, path):
    return HttpResponse(siloname+" "+id+" - "+path, mimetype="text/plain")
    
def subitem_view(request, siloname, id, path, subpath):
    return HttpResponse(siloname+" "+id+" - "+path+" - "+subpath, mimetype="text/plain")
