import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render

import re, os

from rdfdatabank.lib.unpack import store_zipfile, unpack_zip_item, BadZipfile

from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

class PackagesController(BaseController):
    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.silos = ag.authz(granary_list, ident)
        
        return render('/list_of_zipfile_archives.html')
    
    def success(self, message):
        c.message = message
        return render("/success_message.html")

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
            return render("/package_form_upload.html")
        elif http_method == "POST":
            params = request.POST
            if params.has_key("id") and params.has_key("file") and params['id'] and params['file'].filename:
                target_uri = "%s%s" % (c.silo.state['uri_base'], params['id'])
                info = {}
                info['package_filename'] = params['file'].filename
                zip_item = store_zipfile(c.silo, target_uri, params['file'], ident['repoze.who.userid'])
                
                # Broadcast zipfile creation
                ag.b.creation(silo, params['id'], ident=ident['repoze.who.userid'], package_type="zipfile")
                
                info['zip_id'] = zip_item.item_id
                info['zip_uri'] = zip_item.uri
                info['zip_target'] = target_uri
                info['zip_file_stat'] = zip_item.stat(info['package_filename'])
                info['zip_file_size'] = info['zip_file_stat'].st_size
                try:
                    unpack_zip_item(zip_item, c.silo, ident['repoze.who.userid'])
                    
                    # Broadcast derivative creation
                    ag.b.creation(silo, params['id'], ident=ident['repoze.who.userid'])
                    
                    # 302 Redirect to new resource? 201 with Content-Location?
                    # For now, content-location
                    response.headers.add("Content-Location",  target_uri)
                    # conneg return
                    accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                    if not accept_list:
                        accept_list= [MT("text", "html")]
                    mimetype = accept_list.pop(0)
                    while(mimetype):
                        if str(mimetype) in ["text/html", "text/xhtml"]:
                            c.info = info
                            return render('/successful_package_upload.html')
                        elif str(mimetype) == "application/json":
                            response.status_int = 201
                            response.content_type = 'application/json; charset="UTF-8"'
                            return simplejson.dumps(info)
                        elif str(mimetype) in ["application/rdf+xml", "text/xml"]:
                            response.status_int = 201
                            response.content_type = 'application/rdf+xml; charset="UTF-8"'
                            return zip_item.rdf_to_string(format="pretty-xml")
                    # Whoops - nothing satisfies
                    abort(406)
                except BadZipfile:
                    # Bad zip file
                    info['unpacking_status'] = "FAIL - Couldn't unzip package"
                    abort(500, "Couldn't unpack zipfile")
            else:
                abort(400, "You must supply a valid id")
        abort(404)
