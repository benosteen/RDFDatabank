import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import create_new, is_embargoed, get_readme_text, test_rdf

from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

from datetime import datetime, timedelta
from paste.fileapp import FileApp

import re, os

JAILBREAK = re.compile("[\/]*\.\.[\/]*")

import simplejson

log = logging.getLogger(__name__)

class ObjectsController(BaseController):
    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        c.ident = ident
        return render('/list_of_archives.html')
        
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
        c.silo = ag.granary.get_rdf_silo(silo)
        
        http_method = request.environ['REQUEST_METHOD']
        if http_method == "GET":
            c.embargos = {}
            for item in c.silo.list_items():
                c.embargos[item] = is_embargoed(c.silo, item)
            c.items = c.silo.list_items()
            # conneg return
            accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            if not accept_list:
                accept_list= [MT("text", "html")]
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype) in ["text/html", "text/xhtml"]:
                    return render('/siloview.html')
                elif str(mimetype) in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    items = {}
                    for item_id in c.items:
                        items[item_id] = {}
                        items[item_id]['embargo_info'] = c.embargos[item_id]
                    return simplejson.dumps(items)
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                        
            return render('/siloview.html')
        elif http_method == "POST":
            params = request.POST
            if params.has_key("id"):
                if c.silo.exists(params['id']):
                    response.content_type = "text/plain"
                    response.status_int = 409
                    response.status = "409 Conflict: Object Already Exists"
                    return "Object Already Exists"
                else:
                    # Supported params:
                    # id, title, embargoed, embargoed_until, embargo_days_from_now
                    id = params['id']
                    del params['id']
                    item = create_new(c.silo, id, ident['repoze.who.userid'], **params)
                    
                    # Broadcast change as message
                    ag.b.creation(silo, id, ident=ident['repoze.who.userid'])
                    
                    # conneg return
                    accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                    if not accept_list:
                        accept_list= [MT("text", "html")]
                    mimetype = accept_list.pop(0)
                    while(mimetype):
                        if str(mimetype) in ["text/html", "text/xhtml"]:
                            # probably a browser - redirect to newly created object
                            redirect_to(controller="objects", action="itemview", silo=silo, id=id)
                        elif str(mimetype) in ["text/plain"]:
                            response.content_type = "text/plain"
                            response.status_int = 201
                            response.status = "201 Created"
                            #response.headers.add("Content-Location", item.uri)
                            return "Created"
                        try:
                            mimetype = accept_list.pop(0)
                        except IndexError:
                            mimetype = None
                    # Whoops - nothing satisfies
                    response.content_type = "text/plain"
                    response.status_int = 201
                    #response.headers.add("Content-Location", item.uri)
                    response.status = "201 Created"
                    return "Created"
                    
    def itemview(self, silo, id):
        # Check to see if embargo is on:
        c.silo_name = silo
        c.id = id
        c.silo = ag.granary.get_rdf_silo(silo)
        
        c.embargoed = False
        if c.silo.exists(id):
            c.item = c.silo.get_item(id)
        
            if c.item.metadata.get('embargoed') not in ["false", 0, False]:
                c.embargoed = True
        c.embargos = {}
        c.embargos[id] = is_embargoed(c.silo, id)
        http_method = request.environ['REQUEST_METHOD']
        
        c.editor = False
        
        if not (http_method == "GET" and not c.embargoed):
            #identity management if item 
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
        
            c.editor = silo in c.silos
        
        # Method determination
        if http_method == "GET":
            if c.silo.exists(id):
                # conneg:
                c.item = c.silo.get_item(id)
                
                c.parts = c.item.list_parts(detailed=True)
                
                if "README" in c.parts.keys():
                    c.readme_text = get_readme_text(c.item)
                    
                # View options
                options = request.GET
                if "view" in options:
                    c.view = options['view']
                elif c.editor:
                    c.view = 'editor'
                else:
                    c.view = 'user'
                    
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                if not accept_list:
                    accept_list= [MT("text", "html")]
                mimetype = accept_list.pop(0)
                while(mimetype):
                    if str(mimetype) in ["text/html", "text/xhtml"]:
                        return render('/itemview.html')
                    elif str(mimetype) in ["text/plain", "application/json"]:
                        response.content_type = 'application/json; charset="UTF-8"'
                        def serialisable_stat(stat):
                            stat_values = {}
                            for f in ['st_atime', 'st_blksize', 'st_blocks', 'st_ctime', 'st_dev', 'st_gid', 'st_ino', 'st_mode', 'st_mtime', 'st_nlink', 'st_rdev', 'st_size', 'st_uid']:
                                try:
                                    stat_values[f] = stat.__getattribute__(f)
                                except AttributeError:
                                    pass
                            return stat_values
                        items = {}
                        items['parts'] = {}
                        for part in c.parts:
                            items['parts'][part] = serialisable_stat(c.parts[part])
                        if c.readme_text:
                            items['readme_text'] = c.readme_text
                        if c.item.manifest:
                            items['state'] = c.item.manifest.state
                        return simplejson.dumps(items)
                    elif str(mimetype) in ["application/rdf+xml", "text/xml"]:
                        response.content_type = 'application/rdf+xml; charset="UTF-8"'
                        return c.item.rdf_to_string(format="pretty-xml")
                    elif str(mimetype) == "text/rdf+n3":
                        response.content_type = 'text/rdf+n3; charset="UTF-8"'
                        return c.item.rdf_to_string(format="n3")
                    elif str(mimetype) == "application/x-turtle":
                        response.content_type = 'application/x-turtle; charset="UTF-8"'
                        return c.item.rdf_to_string(format="turtle")
                    elif str(mimetype) in ["text/rdf+ntriples", "text/rdf+nt"]:
                        response.content_type = 'text/rdf+ntriples; charset="UTF-8"'
                        return c.item.rdf_to_string(format="nt")
                    # Whoops - nothing satisfies
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                abort(406)
            else:
                abort(404)
        elif http_method == "POST" and c.editor:
            params = request.POST
            if not c.silo.exists(id):
                if 'id' in params.keys():
                    del params['id']
                item = create_new(c.silo, id, ident['repoze.who.userid'], **params)
                
                # Broadcast change as message
                ag.b.creation(silo, id, ident=ident['repoze.who.userid'])
                
                # conneg return
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                if not accept_list:
                    accept_list= [MT("text", "html")]
                mimetype = accept_list.pop(0)
                while(mimetype):
                    if str(mimetype) in ["text/html", "text/xhtml"]:
                        # probably a browser - redirect to newly created object
                        redirect_to(controller="objects", action="itemview", silo=silo, id=id)
                    elif str(mimetype) in ["text/plain"]:
                        response.content_type = "text/plain"
                        response.status_int = 201
                        response.status = "201 Created"
                        #response.headers.add("Content-Location", item.uri)
                        return "Created"
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                # Whoops - nothing satisfies
                response.content_type = "text/plain"
                response.status_int = 201
                #response.headers.add("Content-Location", item.uri)
                response.status = "201 Created"
                return "Created"
            elif params.has_key('embargo_change'):
                item = c.silo.get_item(id)
                if params.has_key('embargoed'):
                    item.metadata['embargoed'] = True
                else:
                    #if is_embargoed(c.silo, id)[0] == True:
                    item.metadata['embargoed'] = False
                if params.has_key('embargoed_until'):
                    item.metadata['embargoed_until'] = params['embargoed_until']
                item.sync()
                e, e_d = is_embargoed(c.silo, id, refresh=True)
                
                # Broadcast change as message
                ag.b.embargo_change(silo, id, item.metadata['embargoed'], item.metadata['embargoed_until'], ident=ident['repoze.who.userid'])
                
                response.content_type = "text/plain"
                response.status_int = 200
                return simplejson.dumps({'embargoed':e, 'embargoed_until':e_d})
            elif params.has_key('file'):
                # File upload by a not-too-savvy method - Service-orientated fallback:
                # Assume file upload to 'filename'
                params = request.POST
                item = c.silo.get_item(id)
                filename = params.get('filename')
                if not filename:
                    filename = params['file'].filename
                upload = params.get('file')
                if JAILBREAK.search(filename) != None:
                    abort(400, "'..' cannot be used in the path or as a filename")
                target_path = filename
                
                if item.isfile(target_path):
                    code = 200
                elif item.isdir(target_path):
                    response.status_int = 403
                    return "Cannot POST a file on to an existing directory"
                else:
                    code = 201
                item.put_stream(target_path, upload.file)
                upload.file.close()
                
                if code == 201:
                    ag.b.creation(silo, id, target_path, ident=ident['repoze.who.userid'])
                else:
                    ag.b.change(silo, id, target_path, ident=ident['repoze.who.userid'])
                response.status_int = code
                # conneg return
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                if not accept_list:
                    accept_list= [MT("text", "html")]
                mimetype = accept_list.pop(0)
                while(mimetype):
                    if str(mimetype) in ["text/html", "text/xhtml"]:
                        redirect_to(controller="objects", action="itemview", id=id, silo=silo)
                    else:
                        response.status_int = code
                        return "Added file %s to item %s" % (filename, id)
            elif params.has_key('text'):
                # Text upload convenience service
                params = request.POST
                item = c.silo.get_item(id)
                filename = params.get('filename')
                if not filename:
                    abort(406, "Must supply a filename")
                
                if JAILBREAK.search(filename) != None:
                    abort(400, "'..' cannot be used in the path or as a filename")
                target_path = filename
                
                if item.isfile(target_path):
                    code = 204
                elif item.isdir(target_path):
                    response.status_int = 403
                    return "Cannot POST a file on to an existing directory"
                else:
                    code = 201
                
                if filename == "manifest.rdf":
                    # valid to make sure it's valid RDF
                    # Otherwise this object will not be accessible
                    text = params['text']
                    if not test_rdf(text):
                        abort(406, "Not able to parse RDF/XML")
                
                item.put_stream(target_path, params['text'].encode("utf-8"))
                
                if code == 201:
                    ag.b.creation(silo, id, target_path, ident=ident['repoze.who.userid'])
                else:
                    ag.b.change(silo, id, target_path, ident=ident['repoze.who.userid'])
                response.status_int = code
                # conneg return
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                if not accept_list:
                    accept_list= [MT("text", "html")]
                mimetype = accept_list.pop(0)
                while(mimetype):
                    if str(mimetype) in ["text/html", "text/xhtml"]:
                        redirect_to(controller="objects", action="itemview", id=id, silo=silo)
                    else:
                        response.status_int = 200
                        return "Added file %s to item %s" % (filename, id)
            else:
                ## TODO apply changeset handling
                ## 1 - store posted CS docs in 'version' "___cs"
                ## 2 - apply changeset to RDF manifest
                ## 3 - update state to reflect latest CS applied
                response.status_int = 204
                return
            
        elif http_method == "DELETE" and c.editor:
            if c.silo.exists(id):
                c.silo.del_item(id)
                
                # Broadcast deletion
                ag.b.deletion(silo, id, ident=ident['repoze.who.userid'])
                
                response.status_int = 200
                return "{'ok':'true'}"   # required for the JQuery magic delete to succede.
            else:
                abort(404)

    def subitemview(self, silo, id, path):
        # Check to see if embargo is on:
        c.silo_name = silo
        c.id = id
        c.silo = ag.granary.get_rdf_silo(silo)
        
        embargoed = False
        if c.silo.exists(id):
            c.item = c.silo.get_item(id)
        
            if c.item.metadata.get('embargoed') not in ["false", 0, False]:
                embargoed = True
        
        http_method = request.environ['REQUEST_METHOD']
        
        c.editor = False
        
        if not (http_method == "GET" and not embargoed):
            #identity management if item 
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
        
            c.editor = silo in c.silos
        
        c.path = path
        
        http_method = request.environ['REQUEST_METHOD']
        
        if http_method == "GET":
            if c.silo.exists(id):
                c.item = c.silo.get_item(id)
                if c.item.isfile(path):
                    fileserve_app = FileApp(c.item.to_dirpath(path))
                    return fileserve_app(request.environ, self.start_response)
                elif c.item.isdir(path):
                    c.parts = c.item.list_parts(path, detailed=True)
                    
                    if "README" in c.parts.keys():
                        c.readme_text = get_readme_text(c.item, "%s/README" % path)
                    accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                    if not accept_list:
                        accept_list= [MT("text", "html")]
                    mimetype = accept_list.pop(0)
                    while(mimetype):
                        if str(mimetype) in ["text/html", "text/xhtml"]:
                            return render("/subitemview.html")
                        elif str(mimetype) in ["text/plain", "application/json"]:
                            def serialisable_stat(stat):
                                stat_values = {}
                                for f in ['st_atime', 'st_blksize', 'st_blocks', 'st_ctime', 'st_dev', 'st_gid', 'st_ino', 'st_mode', 'st_mtime', 'st_nlink', 'st_rdev', 'st_size', 'st_uid']:
                                    try:
                                        stat_values[f] = stat.__getattribute__(f)
                                    except AttributeError:
                                        pass
                                return stat_values
                            response.content_type = "text/plain"
                            items = {}
                            items['parts'] = {}
                            for part in c.parts:
                                items['parts'][part] = serialisable_stat(c.parts[part])
                            if c.readme_text:
                                items['readme_text'] = c.readme_text
                            return simplejson.dumps(items)
                            try:
                                mimetype = accept_list.pop(0)
                            except IndexError:
                                mimetype = None
                    return render("/subitemview.html")
                else:
                    abort(404)
        elif http_method == "PUT" and c.editor:
            if c.silo.exists(id):
                # Pylons loads the request body into request.body...
                # This is not going to work for large files... ah well
                # POST will handle large files as they are pushed to disc,
                # but this won't
                content = request.body
                item = c.silo.get_item(id)
                
                if JAILBREAK.search(path) != None:
                    abort(400, "'..' cannot be used in the path")
                    
                if item.isfile(path):
                    code = 204
                elif item.isdir(path):
                    response.status_int = 403
                    return "Cannot PUT a file on to an existing directory"
                else:
                    code = 201
                
                item.put_stream(path, content)
                
                if code == 201:
                    ag.b.creation(silo, id, path, ident=ident['repoze.who.userid'])
                else:
                    ag.b.change(silo, id, path, ident=ident['repoze.who.userid'])
                
                response.status_int = code
                return
            else:
                # item in which to store file doesn't exist yet...
                # DECISION: Auto-instantiate object and then put file there?
                #           or error out with perhaps a 404?
                # Going with error out...
                response.status_int = 404
                return "Object %s doesn't exist" % id
        elif http_method == "POST" and c.editor:
            if c.silo.exists(id):
                # POST... differences from PUT:
                # path = filepath that this acts on, should be dir, or non-existant
                # if path is a file, this will revert to PUT's functionality and
                # overwrite the file, if there is a multipart file uploaded
                # Expected params: filename, file (uploaded file)
                params = request.POST
                item = c.silo.get_item(id)
                filename = params.get('filename')
                upload = params.get('file')
                if JAILBREAK.search(filename) != None:
                    abort(400, "'..' cannot be used in the path or as a filename")
                target_path = path
                if item.isdir(path) and filename:
                    target_path = os.path.join(path, filename)
                
                if item.isfile(target_path):
                    code = 204
                elif item.isdir(target_path):
                    response.status_int = 403
                    return "Cannot POST a file on to an existing directory"
                else:
                    code = 201
                item.put_stream(target_path, upload.file)
                upload.file.close()
                
                if code == 201:
                    ag.b.creation(silo, id, target_path, ident=ident['repoze.who.userid'])
                else:
                    ag.b.change(silo, id, target_path, ident=ident['repoze.who.userid'])
                response.status_int = code
                return
            else:
                # item doesn't exist yet...
                # DECISION: Auto-instantiate object and then put file there?
                #           or error out with perhaps a 404?
                # Going with error out...
                response.status_int = 404
                return "Object %s doesn't exist" % id
        elif http_method == "DELETE" and c.editor:
            if c.silo.exists(id):
                item = c.silo.get_item(id)
                if item.isfile(path):
                    item.del_stream(path)
                    
                    ag.b.deletion(silo, id, path, ident=ident['repoze.who.userid'])
                    response.status_int = 200
                    return "{'ok':'true'}"   # required for the JQuery magic delete to succede.
                elif item.isdir(path):
                    parts = item.list_parts(path)
                    for part in parts:
                        if item.isdir(os.path.join(path, part)):
                            # TODO implement proper recursive delete, with RDF aggregation
                            # updating
                            abort(400, "Directory is not empty of directories")
                    for part in parts:
                        item.del_stream(os.path.join(path, part))
                        ag.b.deletion(silo, id, os.path.join(path, part), ident=ident['repoze.who.userid'])
                    item.del_stream(path)
                    ag.b.deletion(silo, id, path, ident=ident['repoze.who.userid'])
                    response.status_int = 200
                    return "{'ok':'true'}"   # required for the JQuery magic delete to succede.
                else:
                    abort(404)
            else:
                abort(404)
