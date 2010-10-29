import logging
import os

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import app_globals as ag

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import create_new
from rdfdatabank.lib.file_unpack import check_file_mimetype, BadZipfile, get_zipfiles_in_dataset, unpack_zip_item
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

class ItemsController(BaseController):  
    def siloview(self, silo):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        #ident = request.environ.get('repoze.who.identity')
        #c.ident = ident
        #granary_list = ag.granary.silos
        #c.silos = ag.authz(granary_list, ident)
        #if silo not in c.silos:
        #    abort(403, "Forbidden")
        
        #c.silo_name = silo
        #c.silo = ag.granary.get_rdf_silo(silo)
        #http_method = request.environ['REQUEST_METHOD']
        #items = c.silo.list_items()
        #c.items = {}
        #for i in items:
        #    item = None
        #    item = c.silo.get_item(i)
        #    c.items[i] = get_zipfiles_in_dataset(item)
        #return render("/files_list_of_datasets.html")
        abort(403, "Forbidden")

    def datasetview(self, silo, id):
        c.silo_name = silo
        c.id = id
        
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        if ident:
            c.silos = ag.authz(granary_list, ident)      
            if silo not in c.silos:
                abort(403, "Forbidden")
        else:
            abort(403, "Forbidden")

        c.silo = ag.granary.get_rdf_silo(silo)
        if not c.silo.exists(id):
            abort (403, "Forbidden")

        #c.item is the dataset containing the zip files
        c.item = c.silo.get_item(id)
        item_real_filepath = c.item.to_dirpath()
        #c.parts = c.item.list_parts(detailed=False)

        http_method = request.environ['REQUEST_METHOD']
        if http_method == "GET":
            c.zipfiles = get_zipfiles_in_dataset(c.item)
            return render("/files_list_of_items.html")
        elif http_method == "POST":
            params = request.POST
            if not (params.has_key("filename") and params['filename']):
                abort(400, "You must supply a filename to unpack")

            target_filepath = "%s/%s"%(item_real_filepath, params['filename'])
            if not os.path.isfile(target_filepath):
                abort(404, "File to unpack not found")
            if not check_file_mimetype(target_filepath, 'application/zip'): 
                abort(415, "File is not of type application/zip")

            if params.has_key("id") and params['id']:
                target_dataset_name = params['id']
            else:
                (head, fn) = os.path.split(params['filename'])
                (fn, ext) = os.path.splitext(fn)
                target_dataset_name = "%s-%s"%(id,fn)
            
            if not c.silo.exists(target_dataset_name):
                target_dataset = create_new(c.silo, target_dataset_name, ident['repoze.who.userid'])
            else:
                target_dataset = c.silo.get_item(target_dataset_name)
            
            try:
                unpack_zip_item(target_dataset, c.item, params['filename'], c.silo, ident['repoze.who.userid'])
            except BadZipfile:
                abort(400, "Couldn't unpack zipfile")

            # conneg return
            accept_list = None
            if 'HTTP_ACCEPT' in request.environ:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            if not accept_list:
                accept_list= [MT("text", "html")]
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    # probably a browser - redirect to newly created dataset 
                    redirect_to(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name)
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    response.status_int = 201
                    response.status = "201 Created"
                    new_item = c.silo.get_item(target_dataset_name)
                    #response.headers["Content-Location"] = new_item.uri
                    #response.headers.add("Content-Location", new_item.uri)
                    #response.content_location = item.uri
                    #response.headers['location'] = item.uri
                    #response.location = item.uri
                    return "Created"
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            # Whoops - nothing satisfies - return text/plain
            response.content_type = "text/plain"
            response.status_int = 201
            new_item = c.silo.get_item(target_dataset_name)
            #response.headers.add("Content-Location", new_item.uri)
            response.status = "201 Created"
            return "Created"
            
    def itemview(self, silo, id, path):
        c.silo_name = silo
        c.id = id
        
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        if ident:
            c.silos = ag.authz(granary_list, ident)      
            if silo not in c.silos:
                abort(403, "Forbidden")
        else:
            abort(403, "Forbidden")

        c.silo = ag.granary.get_rdf_silo(silo)
        if not c.silo.exists(id):
            abort (403, "Forbidden")

        #c.item is the dataset containing the zip files
        c.item = c.silo.get_item(id)
        item_real_filepath = c.item.to_dirpath()
        #c.parts = c.item.list_parts(detailed=False)

        http_method = request.environ['REQUEST_METHOD']
        if http_method == "GET":
            c.zipfiles = get_zipfiles_in_dataset(c.item)
            return render("/files_list_of_items.html")
            #abort (403, "Forbidden")
        elif http_method == "POST":
            params = request.POST
            #if not (params.has_key("filename") and params['filename']):
            #    abort(400, "You must supply a filename to unpack")

            if not path:
                abort(400, "You must supply a filename to unpack")

            target_filepath = "%s/%s"%(item_real_filepath, path)
            if not os.path.isfile(target_filepath):
                abort(404, "File to unpack not found")
            if not check_file_mimetype(target_filepath, 'application/zip'): 
                abort(415, "File is not of type application/zip")

            if params.has_key("id") and params['id']:
                target_dataset_name = params['id']
            else:
                (head, fn) = os.path.split(path)
                (fn, ext) = os.path.splitext(fn)
                target_dataset_name = "%s-%s"%(id,fn)
            #target_dataset_name, current_dataset, post_filepath, silo, ident
            try:
                unpack_zip_item(target_dataset_name, c.item, path, c.silo, ident['repoze.who.userid'])
            except BadZipfile:
                abort(400, "Couldn't unpack zipfile")

            # conneg return
            accept_list = None
            if 'HTTP_ACCEPT' in request.environ:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            if not accept_list:
                accept_list= [MT("text", "html")]
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    # probably a browser - redirect to newly created dataset
                    redirect_to(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name)
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    response.status_int = 201
                    response.status = "201 Created"
                    new_item = c.silo.get_item(target_dataset_name)
                    #response.headers.add("Content-Location", new_item.uri)
                    return "Created"
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            # Whoops - nothing satisfies - return text/plain
            response.content_type = "text/plain"
            response.status_int = 201
            new_item = c.silo.get_item(target_dataset_name)
            #response.headers.add("Content-Location", new_item.uri)
            response.status = "201 Created"
            return "Created"
