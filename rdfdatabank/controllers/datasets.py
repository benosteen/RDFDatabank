import logging
import re, os, shutil
import simplejson
from datetime import datetime, timedelta
import time

from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import rest
from paste.fileapp import FileApp
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.utils import create_new, is_embargoed, get_readme_text, test_rdf, munge_manifest, manifest_type, serialisable_stat, allowable_id2
from rdfdatabank.lib.file_unpack import get_zipfiles_in_dataset
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

JAILBREAK = re.compile("[\/]*\.\.[\/]*")

log = logging.getLogger(__name__)

class DatasetsController(BaseController):      
    @rest.restrict('GET', 'POST')
    def siloview(self, silo):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        if not ag.granary.issilo(silo):
            abort(404)
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if silo not in silos:
            abort(403, "Forbidden")
        
        c.silo_name = silo
        c_silo = ag.granary.get_rdf_silo(silo)
        
        http_method = request.environ['REQUEST_METHOD']
        if http_method == "GET":
            c.embargos = {}
            for item in c_silo.list_items():
                c.embargos[item] = is_embargoed(c_silo, item)
            #c.items = c_silo.list_items()
            c.items = c.embargos.keys()
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
                    return render('/siloview.html')
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
            return render('/siloview.html')
        elif http_method == "POST":
            params = request.POST
            if params.has_key("id"):
                if c_silo.exists(params['id']):
                    response.content_type = "text/plain"
                    response.status_int = 409
                    response.status = "409 Conflict: Dataset Already Exists"
                    return "Dataset Already Exists"
                else:
                    # Supported params:
                    # id, title, embargoed, embargoed_until, embargo_days_from_now
                    id = params['id']
                    if not allowable_id2(id):
                        response.content_type = "text/plain"
                        response.status_int = 403
                        response.status = "403 Forbidden"
                        return "Dataset name can contain only the following characters - %s and has to be more than 1 character"%ag.naming_rule
                    del params['id']
                    item = create_new(c_silo, id, ident['repoze.who.userid'], **params)
                    
                    # Broadcast change as message
                    ag.b.creation(silo, id, ident=ident['repoze.who.userid'])
                    
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
                            redirect_to(controller="datasets", action="datasetview", silo=silo, id=id)
                        elif str(mimetype).lower() in ["text/plain", "application/json"]:
                            response.content_type = "text/plain"
                            response.status_int = 201
                            response.status = "201 Created"
                            response.headers["Content-Location"] = url(controller="datasets", action="datasetview", silo=silo, id=id)
                            return "201 Created"
                        try:
                            mimetype = accept_list.pop(0)
                        except IndexError:
                            mimetype = None
                    # Whoops - nothing satisfies - return text/plain
                    response.content_type = "text/plain"
                    response.status_int = 201
                    response.headers["Content-Location"] = url(controller="datasets", action="datasetview", silo=silo, id=id)
                    response.status = "201 Created"
                    return "201 Created"
                    
    @rest.restrict('GET', 'POST', 'DELETE')
    def datasetview(self, silo, id):       
        if not ag.granary.issilo(silo):
            abort(404)
        # Check to see if embargo is on:
        c.silo_name = silo
        c.id = id

        http_method = request.environ['REQUEST_METHOD']

        c_silo = ag.granary.get_rdf_silo(silo)
        
        c.editor = False
        c.version = None
                
        if not (http_method == "GET"):
            #identity management of item 
            if not request.environ.get('repoze.who.identity'):
                abort(401, "Not Authorised")
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            granary_list = ag.granary.silos
            silos = ag.authz(granary_list, ident)      
            if silo not in silos:
                abort(403, "Forbidden")
            c.editor = silo in silos
        elif http_method == "GET":
            if not c_silo.exists(id):
                abort(404)
            item = c_silo.get_item(id)
            embargoed = False
            if item.metadata.get('embargoed') not in ["false", 0, False]:
                embargoed = True
            granary_list = ag.granary.silos
            if embargoed:
                if not request.environ.get('repoze.who.identity'):
                    abort(401, "Not Authorised") 
                ident = request.environ.get('repoze.who.identity')  
                silos = ag.authz(granary_list, ident)      
                if silo not in silos:
                    abort(403, "Forbidden")
                c.editor = silo in silos
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            if ident:
                silos = ag.authz(granary_list, ident)
                c.editor = silo in silos
        
        # Method determination
        if http_method == "GET":
            c.embargos = {}
            c.embargos[id] = is_embargoed(c_silo, id)
            c.parts = item.list_parts(detailed=True)
            c.manifest_pretty = item.rdf_to_string(format="pretty-xml")
            c.manifest = item.rdf_to_string()
            c.zipfiles = get_zipfiles_in_dataset(item)
            c.readme_text = None
            #if item.isfile("README"):
            if "README" in c.parts.keys():
                c.readme_text = get_readme_text(item)
            #if item.manifest:
            #    state = item.manifest.state
                    
            # View options
            options = request.GET
            if "view" in options:
                c.view = options['view']
            elif c.editor:
                c.view = 'editor'
            else:
                c.view = 'user'

            # conneg:
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
                    return render('/datasetview.html')
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    returndata = {}
                    returndata['embargos'] = c.embargos
                    returndata['view'] = c.view
                    returndata['editor'] = c.editor
                    returndata['parts'] = {}
                    for part in c.parts:
                        returndata['parts'][part] = serialisable_stat(c.parts[part])
                    returndata['readme_text'] = c.readme_text
                    returndata['manifest_pretty'] = c.manifest_pretty
                    returndata['manifest'] = c.manifest
                    returndata['zipfiles'] = c.zipfiles
                    #items['state'] = state
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(returndata)
                elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                    response.status_int = 200
                    response.status = "200 OK"
                    response.content_type = 'application/rdf+xml; charset="UTF-8"'
                    return c.manifest_pretty
                elif str(mimetype).lower() == "text/rdf+n3":
                    response.content_type = 'text/rdf+n3; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return item.rdf_to_string(format="n3")
                elif str(mimetype).lower() == "application/x-turtle":
                    response.content_type = 'application/x-turtle; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return item.rdf_to_string(format="turtle")
                elif str(mimetype).lower() in ["text/rdf+ntriples", "text/rdf+nt"]:
                    response.content_type = 'text/rdf+ntriples; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return item.rdf_to_string(format="nt")
                # Whoops - nothing satisfies
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing staisfies - default to text/html
            return render('/datasetview.html')
        elif http_method == "POST" and c.editor:
            params = request.POST
            if not c_silo.exists(id):
                if not allowable_id2(id):
                    response.content_type = "text/plain"
                    response.status_int = 403
                    response.status = "403 Forbidden"
                    return "Dataset name can contain only the following characters - %s and has to be more than 1 character"%ag.naming_rule
                if 'id' in params.keys():
                    del params['id']
                item = create_new(c_silo, id, ident['repoze.who.userid'], **params)
                
                # Broadcast change as message
                ag.b.creation(silo, id, ident=ident['repoze.who.userid'])
                
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
                        # probably a browser - redirect to newly created dataset
                        redirect_to(controller="datasets", action="datasetview", silo=silo, id=id)
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        response.status_int = 201
                        response.status = "201 Created"
                        response.headers["Content-Location"] = url(controller="datasets", action="datasetview", silo=silo, id=id) 
                        return "201 Created"
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                # Whoops - nothing satisfies - return text/plain
                response.content_type = "text/plain"
                response.status_int = 201
                response.headers["Content-Location"] = url(controller="datasets", action="datasetview", silo=silo, id=id) 
                response.status = "201 Created"
                return "201 Created"
            elif params.has_key('embargo_change') or params.has_key('embargoed'):
                item = c_silo.get_item(id)
                item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                #if params.has_key('embargoed'):
                if (params.has_key('embargo_change') and params.has_key('embargoed')) or \
                   (params.has_key('embargoed') and params['embargoed'].lower() == 'true'):
                    if params.has_key('embargoed_until') and params['embargoed_until']:
                        embargoed_until_date = params['embargoed_until']
                    elif params.has_key('embargo_days_from_now') and params['embargo_days_from_now']:
                        embargoed_until_date = (datetime.now() + timedelta(days=params['embargo_days_from_now'])).isoformat()
                    else:
                        embargoed_until_date = (datetime.now() + timedelta(days=365*70)).isoformat()
                    item.metadata['embargoed'] = True
                    item.metadata['embargoed_until'] = embargoed_until_date
                    item.del_triple(item.uri, u"oxds:isEmbargoed")
                    item.del_triple(item.uri, u"oxds:embargoedUntil")
                    item.add_triple(item.uri, u"oxds:isEmbargoed", 'True')
                    item.add_triple(item.uri, u"oxds:embargoedUntil", embargoed_until_date)
                else:
                    #if is_embargoed(c_silo, id)[0] == True:
                    item.metadata['embargoed'] = False
                    item.metadata['embargoed_until'] = ''
                    item.del_triple(item.uri, u"oxds:isEmbargoed")
                    item.del_triple(item.uri, u"oxds:embargoedUntil")
                    item.add_triple(item.uri, u"oxds:isEmbargoed", 'False')
                item.del_triple(item.uri, u"dcterms:modified")
                item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                item.del_triple(item.uri, u"oxds:currentVersion")
                item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
                item.sync()
                item.sync()
                e, e_d = is_embargoed(c_silo, id, refresh=True)
                
                # Broadcast change as message
                ag.b.embargo_change(silo, id, item.metadata['embargoed'], item.metadata['embargoed_until'], ident=ident['repoze.who.userid'])
                
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
                        redirect_to(controller="datasets", action="datasetview", id=id, silo=silo)
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        response.status_int = 204
                        response.status = "204 Updated"
                        return
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                #Whoops - nothing satisfies - return text / plain
                response.content_type = "text/plain"
                response.status_int = 204
                response.status = "204 Updated"
                return
            elif params.has_key('file'):
                # File upload by a not-too-savvy method - Service-orientated fallback:
                # Assume file upload to 'filename'
                params = request.POST
                item = c_silo.get_item(id)
                filename = params.get('filename')
                if not filename:
                    filename = params['file'].filename
                upload = params.get('file')
                if JAILBREAK.search(filename) != None:
                    abort(400, "'..' cannot be used in the path or as a filename")
                target_path = filename
                
                if item.isfile(target_path):
                    code = 204
                elif item.isdir(target_path):
                    response.content_type = "text/plain"
                    response.status_int = 403
                    response.status = "403 Forbidden"
                    return "Cannot POST a file on to an existing directory"
                else:
                    code = 201

                if filename == "manifest.rdf":
                    #Copy the uploaded file to a tmp area 
                    mani_file = os.path.join('/tmp', filename.lstrip(os.sep))
                    mani_file_obj = open(mani_file, 'w')
                    shutil.copyfileobj(upload.file, mani_file_obj)
                    upload.file.close()
                    mani_file_obj.close()
                    #test rdf file
                    mani_file_obj = open(mani_file, 'r')
                    manifest_str = mani_file_obj.read()
                    mani_file_obj.close()
                    if not test_rdf(manifest_str):
                        response.status_int = 400
                        return "Bad manifest file"
                    #munge rdf
                    item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                    a = item.get_rdf_manifest()
                    b = a.to_string()
                    mtype = manifest_type(b)
                    if not mtype:
                        mtype = 'http://vocab.ox.ac.uk/dataset/schema#Grouping'
                    munge_manifest(manifest_str, item, manifest_type=mtype)
                else:
                    if code == 204:
                        item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf', filename])
                    else:
                        item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                    item.put_stream(target_path, upload.file)
                    upload.file.close()
                item.del_triple(item.uri, u"dcterms:modified")
                item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                item.del_triple(item.uri, u"oxds:currentVersion")
                item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
                item.sync()
                
                if code == 201:
                    ag.b.creation(silo, id, target_path, ident=ident['repoze.who.userid'])
                    response.status = "201 Created"
                    response.status_int = 201
                    response.headers["Content-Location"] = url(controller="datasets", action="itemview", id=id, silo=silo, path=filename)
                    response_message = "201 Created. Added file %s to item %s" % (filename, id)
                else:
                    ag.b.change(silo, id, target_path, ident=ident['repoze.who.userid'])
                    response.status = "204 Updated"
                    response.status_int = 204
                    response_message = None

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
                        redirect_to(controller="datasets", action="datasetview", id=id, silo=silo)
                    elif str(mimetype).lower() in ["text/plain"]:
                        response.content_type = "text/plain"
                        return response_message
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                #Whoops - nothing satisfies - return text / plain
                response.content_type = "text/plain"
                return response_message
            elif params.has_key('text'):
                # Text upload convenience service
                params = request.POST
                item = c_silo.get_item(id)
                filename = params.get('filename')
                if not filename:
                    abort(406, "Must supply a filename")
                
                if JAILBREAK.search(filename) != None:
                    abort(400, "'..' cannot be used in the path or as a filename")
                target_path = filename
                
                if item.isfile(target_path):
                    code = 204
                elif item.isdir(target_path):
                    response.content_type = "text/plain"
                    response.status_int = 403
                    response.status = "403 forbidden"
                    return "Cannot POST a file on to an existing directory"
                else:
                    code = 201
                
                if filename == "manifest.rdf":
                    # valid to make sure it's valid RDF
                    # Otherwise this dataset will not be accessible
                    text = params['text']
                    if not test_rdf(text):
                        abort(406, "Not able to parse RDF/XML")
                    item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                    a = item.get_rdf_manifest()
                    b = a.to_string()
                    mtype = manifest_type(b)
                    if not mtype:
                        mtype = 'http://vocab.ox.ac.uk/dataset/schema#Grouping'
                    munge_manifest(text, item, manifest_type=mtype)
                else:
                    if code == 204:
                        item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf', filename])
                    else:
                        item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                    item.put_stream(target_path, params['text'].encode("utf-8"))
                item.del_triple(item.uri, u"dcterms:modified")
                item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                item.del_triple(item.uri, u"oxds:currentVersion")
                item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
                item.sync()
                
                if code == 201:
                    ag.b.creation(silo, id, target_path, ident=ident['repoze.who.userid'])
                    response.status = "201 Created"
                    response.status_int = 201
                    response.headers["Content-Location"] = url(controller="datasets", action="datasetview", id=id, silo=silo)
                    response_message = "201 Created. Added file %s to item %s" % (filename, id)
                else:
                    ag.b.change(silo, id, target_path, ident=ident['repoze.who.userid'])
                    response.status = "204 Updated"
                    response.status_int = 204
                    response_message = None
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
                        redirect_to(controller="datasets", action="datasetview", id=id, silo=silo)
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        return response_message
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                #Whoops - nothing satisfies - return text / plain
                response.content_type = "text/plain"
                return response_message
            else:
                response.content_type = "text/plain"
                response.status_int = 403
                response.status = "403 Forbidden"
                return "403 Forbidden"
        elif http_method == "DELETE" and c.editor:
            if c_silo.exists(id):
                c_silo.del_item(id)
                
                # Broadcast deletion
                ag.b.deletion(silo, id, ident=ident['repoze.who.userid'])
                
                response.content_type = "text/plain"
                response.status_int = 200
                response.status = "200 OK"
                return "{'ok':'true'}"   # required for the JQuery magic delete to succede.
            else:
                abort(404)

    @rest.restrict('GET') 
    def datasetview_vnum(self, silo, id, vnum):       
        if not ag.granary.issilo(silo):
            abort(404)
        c.silo_name = silo
        c.id = id
        c_silo = ag.granary.get_rdf_silo(silo)
        
        if not c_silo.exists(id):
            abort(404)

        item = c_silo.get_item(id)
        vnum = str(vnum)
        if not vnum in item.manifest['versions']:
            abort(404)

        # filename options - used to check if DOI redirects the parameters
        c.options = request.GET

        #Set the item's version cursor
        item.set_version_cursor(vnum)
        c.version = vnum           

        embargoed = False
        c.editor = False 
        if item.metadata.get('embargoed') not in ["false", 0, False]:
            embargoed = True
        if embargoed:
            if not request.environ.get('repoze.who.identity'):
                abort(401, "Not Authorized")
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            granary_list = ag.granary.silos
            silos = ag.authz(granary_list, ident)
            if silo not in silos:
                abort(403, "Forbidden")
            c.editor = silo in silos
        elif request.environ.get('repoze.who.identity'):
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            granary_list = ag.granary.silos
            silos = ag.authz(granary_list, ident)
            c.editor = silo in silos

        # Check to see if embargo is on:        
        c.embargos = {}
        c.embargos[id] = is_embargoed(c_silo, id)
        c.readme_text = None
        c.parts = item.list_parts(detailed=True)
        c.manifest_pretty = item.rdf_to_string(format="pretty-xml")
        if "README" in c.parts.keys():
            c.readme_text = get_readme_text(item)
                 
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
                return render('/datasetview_version.html')
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                response.content_type = 'application/json; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                returndata = {}
                returndata['embargos'] = c.embargos
                returndata['view'] = c.view
                returndata['editor'] = c.editor
                returndata['parts'] = {}
                for part in c.parts:
                    returndata['parts'][part] = serialisable_stat(c.parts[part])
                returndata['readme_text'] = c.readme_text
                returndata['manifest_pretty'] = c.manifest_pretty
                return simplejson.dumps(returndata)
            elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                response.content_type = 'application/rdf+xml; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return c.manifest_pretty
            elif str(mimetype).lower() == "text/rdf+n3":
                response.content_type = 'text/rdf+n3; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return item.rdf_to_string(format="n3")
            elif str(mimetype).lower() == "application/x-turtle":
                response.content_type = 'application/x-turtle; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return item.rdf_to_string(format="turtle")
            elif str(mimetype).lower() in ["text/rdf+ntriples", "text/rdf+nt"]:
                response.content_type = 'text/rdf+ntriples; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return item.rdf_to_string(format="nt")
            # Whoops - nothing satisfies
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops - nothing staisfies - default to text/html
        return render('/datasetview_version.html')

    @rest.restrict('GET', 'POST', 'PUT', 'DELETE')
    def itemview(self, silo, id, path):
        if not ag.granary.issilo(silo):
            abort(404)
        # Check to see if embargo is on:
        c.silo_name = silo
        c.id = id
        c.version = None
        c.path = path
        c_silo = ag.granary.get_rdf_silo(silo)
        
        if not c_silo.exists(id):
            # dataset doesn't exist yet...
            # DECISION FOR POST / PUT : Auto-instantiate dataset and then put file there?
            #           or error out with perhaps a 404?
            # Going with error out...
            abort(404)
        
        embargoed = False
        item = c_silo.get_item(id)        
        if item.metadata.get('embargoed') not in ["false", 0, False]:
            embargoed = True
        
        http_method = request.environ['REQUEST_METHOD']
        
        editor = False
        granary_list = ag.granary.silos
        if not (http_method == "GET"):
            #identity management if item 
            if not request.environ.get('repoze.who.identity'):
                abort(401, "Not Authorised")
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            silos = ag.authz(granary_list, ident)      
            if silo not in silos:
                abort(403, "Forbidden")
            editor = silo in silos
        elif embargoed:
            if not request.environ.get('repoze.who.identity'):
                abort(401, "Not Authorised")  
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            silos = ag.authz(granary_list, ident)      
            if silo not in silos:
                abort(403, "Forbidden")
            editor = silo in silos
        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident
        if ident:
            silos = ag.authz(granary_list, ident)
            editor = silo in silos
        
        if http_method == "GET":
            if item.isfile(path):
                fileserve_app = FileApp(item.to_dirpath(path))
                return fileserve_app(request.environ, self.start_response)
            elif item.isdir(path):
                #c.parts = item.list_parts(detailed=True)
                c.parts = item.list_parts(path, detailed=True)
                c.readme_text = None
                if "README" in c.parts.keys():
                    c.readme_text = get_readme_text(item, "%s/README" % path)
                    
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
                        return render("/itemview.html")
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = 'application/json; charset="UTF-8"'
                        response.status_int = 200
                        response.status = "200 OK"
                        returndata = {}
                        returndata['parts'] = {}
                        for part in c.parts:
                            returndata['parts'][part] = serialisable_stat(c.parts[part])
                        returndata['readme_text'] = c.readme_text
                        return simplejson.dumps(returndata)
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                #Whoops - nothing satisfies - return text/html
                return render("/itemview.html")
            else:
                abort(404)
        elif http_method == "PUT" and editor:
            # Pylons loads the request body into request.body...
            # This is not going to work for large files... ah well
            # POST will handle large files as they are pushed to disc,
            # but this won't
            content = request.body
            item = c_silo.get_item(id)
                
            if JAILBREAK.search(path) != None:
                abort(400, "'..' cannot be used in the path")
                    
            if item.isfile(path):
                code = 204
            elif item.isdir(path):
                response.content_type = "text/plain"
                response.status_int = 403
                response.status = "403 Forbidden"
                return "Cannot PUT a file on to an existing directory"
            else:
                code = 201

            #Check if path is manifest.rdf - If, yes Munge
            if "manifest.rdf" in path:
                #test content is valid rdf
                if not test_rdf(content):
                    response.status_int = 400
                    return "Bad manifest file"
                #munge rdf
                item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                a = item.get_rdf_manifest()
                b = a.to_string()
                mtype = manifest_type(b)
                if not mtype:
                    mtype = 'http://vocab.ox.ac.uk/dataset/schema#Grouping'
                munge_manifest(content, item, manifest_type=mtype)
            else:
                if code == 204:
                    item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf', path])
                else:
                    item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                item.put_stream(path, content)
            item.del_triple(item.uri, u"dcterms:modified")
            item.add_triple(item.uri, u"dcterms:modified", datetime.now())
            item.del_triple(item.uri, u"oxds:currentVersion")
            item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
            item.sync()
                
            if code == 201:
                ag.b.creation(silo, id, path, ident=ident['repoze.who.userid'])
                response.status = "201 Created"
                response.status_int = 201
                response.headers["Content-Location"] = url(controller="datasets", action="itemview", id=id, silo=silo, path=path)
                response_message = "201 Created"
            else:
                ag.b.change(silo, id, path, ident=ident['repoze.who.userid'])
                response.status = "204 Updated"
                response.status_int = 204
                response_message = None
            
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
                    redirect_to(controller="datasets", action="itemview", id=id, silo=silo, path=path)
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    return response_message
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing satisfies - return text / plain
            response.content_type = "text/plain"
            return response_message
        elif http_method == "POST" and editor:
            # POST... differences from PUT:
            # path = filepath that this acts on, should be dir, or non-existant
            # if path is a file, this will revert to PUT's functionality and
            # overwrite the file, if there is a multipart file uploaded
            # Expected params: filename, file (uploaded file)
            params = request.POST
            item = c_silo.get_item(id)
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
                response.content_type = "text/plain"
                response.status_int = 403
                response.status = "403 Forbidden"
                return "Cannot POST a file on to an existing directory"
            else:
                code = 201

            if filename == "manifest.rdf":
                #Copy the uploaded file to a tmp area 
                mani_file = os.path.join('/tmp', filename.lstrip(os.sep))
                mani_file_obj = open(mani_file, 'w')
                shutil.copyfileobj(upload.file, mani_file_obj)
                upload.file.close()
                mani_file_obj.close()
                #test rdf file
                mani_file_obj = open(mani_file, 'r')
                manifest_str = mani_file_obj.read()
                mani_file_obj.close()
                if not test_rdf(manifest_str):
                    response.status_int = 400
                    return "Bad manifest file"
                #munge rdf
                item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                a = item.get_rdf_manifest()
                b = a.to_string()
                mtype = manifest_type(b)
                if not mtype:
                    mtype = 'http://vocab.ox.ac.uk/dataset/schema#Grouping'
                munge_manifest(manifest_str, item, manifest_type=mtype)
            else:
                if code == 204:
                    item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf', filename])
                else:
                    item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])                
                item.put_stream(target_path, upload.file)
                upload.file.close()
            item.del_triple(item.uri, u"dcterms:modified")
            item.add_triple(item.uri, u"dcterms:modified", datetime.now())
            item.del_triple(item.uri, u"oxds:currentVersion")
            item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
            item.sync()
                
            if code == 201:
                ag.b.creation(silo, id, target_path, ident=ident['repoze.who.userid'])
                response.status = "201 Created"
                response.status_int = 201
                response.headers["Content-Location"] = url(controller="datasets", action="itemview", id=id, silo=silo, path=path)
                response_message = "201 Created"
            else:
                ag.b.change(silo, id, target_path, ident=ident['repoze.who.userid'])
                response.status = "204 Updated"
                response.status_int = 204
                response_message = None

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
                    redirect_to(controller="datasets", action="itemview", id=id, silo=silo, path=path)
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    return response_message
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing satisfies - return text / plain
            response.content_type = "text/plain"
            return response_message
        elif http_method == "DELETE" and editor:
            item = c_silo.get_item(id)
            if item.isfile(path):
                if 'manifest.rdf' in path:
                    response.content_type = "text/plain"
                    response.status_int = 403
                    response.status = "403 Forbidden"
                    return "Forbidden - Cannot delete the manifest"
                item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                item.del_stream(path)
                item.del_triple(item.uri, u"dcterms:modified")
                item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                item.del_triple(item.uri, u"oxds:currentVersion")
                item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
                item.sync()
                ag.b.deletion(silo, id, path, ident=ident['repoze.who.userid'])
                response.content_type = "text/plain"
                response.status_int = 200
                response.status = "200 OK"
                return "{'ok':'true'}"   # required for the JQuery magic delete to succede.
            elif item.isdir(path):
                item.increment_version_delta(clone_previous_version=True, copy_filenames=['manifest.rdf'])
                item.del_triple(item.uri, u"oxds:currentVersion")
                item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
                item.del_dir(path)
                item.del_triple(item.uri, u"dcterms:modified")
                item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                item.sync()
                ag.b.deletion(silo, id, path, ident=ident['repoze.who.userid'])
                response.content_type = "text/plain"
                response.status_int = 200
                response.status = "200 OK"
                return "{'ok':'true'}"   # required for the JQuery magic delete to succede.
            else:
                abort(404)

    @rest.restrict('GET')
    def itemview_vnum(self, silo, id, path, vnum):
        if not ag.granary.issilo(silo):
            abort(404)
        # Check to see if embargo is on:
        c.silo_name = silo
        c.id = id
        c.version = vnum
        c.path = path 
        c_silo = ag.granary.get_rdf_silo(silo)

        if not c_silo.exists(id):
            # dataset doesn't exist
            abort(404)
        
        item = c_silo.get_item(id)
        vnum = str(vnum)
        if not vnum in item.manifest['versions']:
            abort(404)
        item.set_version_cursor(vnum)

        embargoed = False        
        if item.metadata.get('embargoed') not in ["false", 0, False]:
            embargoed = True
        
        if embargoed:
            #identity management if item 
            if not request.environ.get('repoze.who.identity'):
                abort(401, "Not Authorised")
            ident = request.environ.get('repoze.who.identity')  
            c.ident = ident
            granary_list = ag.granary.silos
            silos = ag.authz(granary_list, ident)      
            if silo not in silos:
                abort(403, "Forbidden")
        
        if item.isfile(path):
            fileserve_app = FileApp(item.to_dirpath(path))
            return fileserve_app(request.environ, self.start_response)
        elif item.isdir(path):
            c.parts = item.list_parts(path, detailed=True)
            c.readme_text = None
            if "README" in c.parts.keys():
                c.readme_text = get_readme_text(item, "%s/README" % path)
                    
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
                    return render("/itemview_version.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    returndata = {}
                    returndata['parts'] = {}
                    for part in c.parts:
                        returndata['parts'][part] = serialisable_stat(c.parts[part])
                    returndata['readme_text'] = c.readme_text
                    return simplejson.dumps(returndata)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing satisfies - return text/html
            return render("/itemview_version.html")
        else:
            abort(404)
