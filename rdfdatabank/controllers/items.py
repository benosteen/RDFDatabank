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
import os, time
from datetime import datetime, timedelta
import simplejson
from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort, redirect
from pylons.decorators import rest

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import create_new, allowable_id2
from rdfdatabank.lib.file_unpack import check_file_mimetype, BadZipfile, get_zipfiles_in_dataset, unpack_zip_item, read_zipfile
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

class ItemsController(BaseController):  
    def siloview(self, silo):
        abort(403, "Forbidden")

    @rest.restrict('GET', 'POST')
    def datasetview(self, silo, id):
        """Get a list of zipfiles in dataset 'id' within the silo 'silo' and unpack a dataset."""
                
        if not ag.granary.issilo(silo):
            abort(404)
            
        rdfsilo = ag.granary.get_rdf_silo(silo)
        if not rdfsilo.exists(id):
            abort (404)
            
        #tmpl_context variables needed: c.silo_name, c.zipfiles, c.ident, c.id, c.path
        c.silo_name = silo
        c.id = id
        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        dataset = rdfsilo.get_item(id)

        creator = None
        if dataset.manifest and dataset.manifest.state and 'metadata' in dataset.manifest.state and dataset.manifest.state['metadata'] and \
            'createdby' in dataset.manifest.state['metadata'] and dataset.manifest.state['metadata']['createdby']:
            creator = dataset.manifest.state['metadata']['createdby']

        http_method = request.environ['REQUEST_METHOD']
        
        if http_method == "GET":
            c.editor = False
            if ag.metadata_embargoed:
                if not ident:
                    abort(401, "Not Authorised")
                silos = ag.authz(granary_list, ident)
                if silo not in silos:
                    abort(403, "Forbidden")
                if ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]:
                    c.editor = True
            elif ident:
                silos = ag.authz(granary_list, ident)
                if silo in silos:
                    if ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]:
                        c.editor = True
        else:
            #identity management of item 
            if not ident:
                abort(401, "Not Authorised")
            silos = ag.authz(granary_list, ident)      
            if silo not in silos:
                abort(403, "Forbidden")
            if not (ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]):
                abort(403, "Forbidden")

        if http_method == "GET":
            c.zipfiles = get_zipfiles_in_dataset(dataset)
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
                    return render("/list_of_zipfiles.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    #return simplejson.dumps(dict(c.zipfiles))
                    return simplejson.dumps(list(c.zipfiles.keys()))
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/html            
            return render("/list_of_zipfiles.html")
        elif http_method == "POST":
            params = request.POST
            if not (params.has_key("filename") and params['filename']):
                abort(400, "You must supply a filename to unpack")

            item_real_filepath = dataset.to_dirpath()
            target_filepath = "%s/%s"%(item_real_filepath, params['filename'])
            if not os.path.isfile(target_filepath):
                abort(404, "File to unpack not found")
            if not check_file_mimetype(target_filepath, 'application/zip'): 
                abort(415, "File is not of type application/zip")

            if params.has_key("id") and params['id']:
                target_dataset_name = params['id']
            else:
                #(head, fn) = os.path.split(params['filename'])
                #(fn, ext) = os.path.splitext(fn)
                #target_dataset_name = "%s-%s"%(id,fn)
                target_dataset_name = id

            #step 1: Create / initialize target dataset 
            if not rdfsilo.exists(target_dataset_name):
                if not allowable_id2(target_dataset_name):
                    response.content_type = "text/plain"
                    response.status_int = 400
                    response.status = "400 Bad request. Dataset name not valid"
                    return "Dataset name can contain only the following characters - %s and has to be more than 1 character"%ag.naming_rule
                target_dataset = create_new(rdfsilo, target_dataset_name, ident['repoze.who.userid'])
                response.status_int = 201
                response.status = "201 Created"
                response.headers["Content-Location"] = url(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name)
                response_message = "201 Created"
            else:
                target_dataset = rdfsilo.get_item(target_dataset_name)
                response.status = "204 Updated"
                response.status_int = 204
                response_message = None

            #step 2: Unpack zip item 
            try:
                unpack_zip_item(target_dataset, dataset, params['filename'], rdfsilo, ident['repoze.who.userid'])
            except BadZipfile:
                abort(400, "BadZipfile: Couldn't unpack zipfile")

            target_dataset.sync()
            target_dataset.sync()
            target_dataset.sync()

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
                    redirect(url(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name))
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    return response_message
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            # Whoops - nothing satisfies - return text/plain
            response.content_type = "text/plain"
            return response_message
 
    @rest.restrict('GET', 'POST')
    def itemview(self, silo, id, path):
        """API call to read the contents of a zip-file (without having to unpack) and unpack a zip file into a new / existing dataset"""
        #tmpl_context variables needed: c.silo_name, c.zipfile_contents c.ident, c.id, c.path       
        if not path:
            abort(400, "You must supply a filename to unpack")
            
        if not ag.granary.issilo(silo):
            abort(404)

        rdfsilo = ag.granary.get_rdf_silo(silo)
        if not rdfsilo.exists(id):
            abort (404)

        c.silo_name = silo
        c.id = id
        c.path = path

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        dataset = rdfsilo.get_item(id)
                    
        creator = None
        if dataset.manifest and dataset.manifest.state and 'metadata' in dataset.manifest.state and dataset.manifest.state['metadata'] and \
            'createdby' in dataset.manifest.state['metadata'] and dataset.manifest.state['metadata']['createdby']:
            creator = dataset.manifest.state['metadata']['createdby']

        http_method = request.environ['REQUEST_METHOD']
        
        if http_method == "GET":
            if dataset.metadata.get('embargoed') not in ["false", 0, False]:
                if not ident:
                    abort(401, "Not Authorised")
                silos = ag.authz(granary_list, ident)
                if silo not in silos:
                    abort(403, "Forbidden")
        else: 
            if not ident:
                abort(401, "Not Authorised")
            silos = ag.authz(granary_list, ident)
            if silo not in silos:
                abort(403, "Forbidden")     
            if not (ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]):
                abort(403, "Forbidden")

        item_real_filepath = dataset.to_dirpath()
        target_filepath = "%s/%s"%(item_real_filepath, path)
        #c.parts = dataset.list_parts(detailed=False)
        if not dataset.isfile(path):
            abort(404, "File not found")
        if not os.path.isfile(target_filepath):
            abort(404, "File not found")
        if not check_file_mimetype(target_filepath, 'application/zip'): 
            abort(415, "File is not of type application/zip")
                
        if http_method == "GET":
            try:
                c.zipfile_contents = read_zipfile(target_filepath)
            except BadZipfile:
                abort(400, "Could not read zipfile")
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
                    return render("/zipfileview.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(c.zipfile_contents)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            # Whoops - nothing satisfies - return text/html
            return render("/zipfileview.html")
        elif http_method == "POST":
            params = request.POST
            #if not (params.has_key("filename") and params['filename']):
            #    abort(400, "You must supply a filename to unpack")

            if params.has_key("id") and params['id']:
                target_dataset_name = params['id']
            else:
                #(head, fn) = os.path.split(path)
                #(fn, ext) = os.path.splitext(fn)
                #target_dataset_name = "%s-%s"%(id,fn)
                target_dataset_name = id

            #step 1: Create / initialize target dataset 
            if not rdfsilo.exists(target_dataset_name):
                if not allowable_id2(target_dataset_name):
                    response.content_type = "text/plain"
                    response.status_int = 400
                    response.status = "400 Bad request. Dataset name not valid"
                    return "Dataset name can contain only the following characters - %s and has to be more than 1 character"%ag.naming_rule
                target_dataset = create_new(rdfsilo, target_dataset_name, ident['repoze.who.userid'])
                response.status_int = 201
                response.status = "201 Created"
                response.headers["Content-Location"] = url(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name)
                response_message = "201 Created"
            else:
                target_dataset = rdfsilo.get_item(target_dataset_name)
                response.status = "204 Updated"
                response.status_int = 204
                response_message = None
            
            #step 2: Unpack zip item 
            try:
                unpack_zip_item(target_dataset_name, dataset, path, rdfsilo, ident['repoze.who.userid'])
            except BadZipfile:
                abort(400, "Couldn't unpack zipfile")
            
            target_dataset.sync()
            target_dataset.sync()
            target_dataset.sync()

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
                    redirect(url(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name))
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    return response_message
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            # Whoops - nothing satisfies - return text/plain
            response.content_type = "text/plain"
            return response_message

    @rest.restrict('GET')
    def subitemview(self, silo, id, path, subpath):
        #Function to retreive a file from the zipfile
        #TODO 
        #    I check to see the path is avlid and it is a zip file.
        #    I do not deal with subpath. if it is a file - serve it. If it is a dir, show the contents of it.

        #tmpl_context variables needed: c.silo_name, c.zipfile_contents c.ident, c.id, c.path       
        if not ag.granary.issilo(silo):
            abort(404)

        if not (path or subpath):
            abort(400, "You must supply a filename to unpack")

        rdfsilo = ag.granary.get_rdf_silo(silo)
        if not rdfsilo.exists(id):
            abort (404)

        c.silo_name = silo
        c.id = id
        c.path = path
        c.subpath = subpath

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        dataset = rdfsilo.get_item(id)

        if dataset.metadata.get('embargoed') not in ["false", 0, False]:
            if not ident:
                abort(401, "Not Authorised")
            silos = ag.authz(granary_list, ident)
            if silo not in silos:
                abort(403, "Forbidden")
                    
        item_real_filepath = dataset.to_dirpath()
        target_filepath = "%s/%s"%(item_real_filepath, path)
        #c.parts = dataset.list_parts(detailed=False)
        if not dataset.isfile(path):
            abort(404, "File not found")
        if not os.path.isfile(target_filepath):
            abort(404, "File not found")
        if not check_file_mimetype(target_filepath, 'application/zip'): 
            abort(415, "File is not of type application/zip")

        #TODO : if subpath is a file - serve it. If subpath is a dir, show the contents of the dir

        return render("/zipfilesubitemview.html")

