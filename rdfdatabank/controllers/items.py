import logging
import os, time
from datetime import datetime, timedelta
import simplejson
from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import rest

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import create_new
from rdfdatabank.lib.file_unpack import check_file_mimetype, BadZipfile, get_zipfiles_in_dataset, unpack_zip_item, read_zipfile
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

class ItemsController(BaseController):  
    def siloview(self, silo):
        abort(403, "Forbidden")

    @rest.restrict('GET', 'POST')
    def datasetview(self, silo, id):
        #tmpl_context variables needed: c.silo_name, c.zipfiles, c.ident, c.id, c.path
        c.silo_name = silo
        c.id = id
        
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)      
        if silo not in silos:
            abort(403, "Forbidden")

        rdfsilo = ag.granary.get_rdf_silo(silo)
        if not rdfsilo.exists(id):
            abort (404)

        dataset = rdfsilo.get_item(id)

        http_method = request.environ['REQUEST_METHOD']
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
                (head, fn) = os.path.split(params['filename'])
                (fn, ext) = os.path.splitext(fn)
                target_dataset_name = "%s-%s"%(id,fn)

            #step 1: Create / initialize target dataset 
            if not rdfsilo.exists(target_dataset_name):
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
                    redirect_to(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name)
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
        #tmpl_context variables needed: c.silo_name, c.zipfile_contents c.ident, c.id, c.path
        c.silo_name = silo
        c.id = id
        c.path = path

        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")

        if not path:
            abort(400, "You must supply a filename to unpack")

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)      
        if silo not in silos:
            abort(403, "Forbidden")

        rdfsilo = ag.granary.get_rdf_silo(silo)
        if not rdfsilo.exists(id):
            abort (404)

        dataset = rdfsilo.get_item(id)
        item_real_filepath = dataset.to_dirpath()
        target_filepath = "%s/%s"%(item_real_filepath, path)
        #c.parts = dataset.list_parts(detailed=False)
        if not dataset.isfile(path):
            abort(404, "File not found")
        if not os.path.isfile(target_filepath):
            abort(404, "File not found")
        if not check_file_mimetype(target_filepath, 'application/zip'): 
            abort(415, "File is not of type application/zip")

        http_method = request.environ['REQUEST_METHOD']
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
                (head, fn) = os.path.split(path)
                (fn, ext) = os.path.splitext(fn)
                target_dataset_name = "%s-%s"%(id,fn)

            #step 1: Create / initialize target dataset 
            if not rdfsilo.exists(target_dataset_name):
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
                    redirect_to(controller="datasets", action="datasetview", silo=silo, id=target_dataset_name)
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
        #tmpl_context variables needed: c.silo_name, c.zipfile_contents c.ident, c.id, c.path
        c.silo_name = silo
        c.id = id
        c.path = path
        c.subpath = subpath

        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")

        if not (path or subpath):
            abort(400, "You must supply a filename to unpack")
 
        return render("/zipfilesubitemview.html")

