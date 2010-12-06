import logging

from pylons import request, response, session, config, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render

import re, os

from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

accepted_params = ['title', 'description', 'notes', 'owners', 'disk_allocation']

class AdminController(BaseController):

    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        c.granary_list = ag.granary.silos
        
        # Admin only
        if ident.get('role') == "admin":
            http_method = request.environ['REQUEST_METHOD']
            if http_method == "GET":
                c.granary = ag.granary
                return render("/silo_admin.html")
            elif http_method == "POST":
                params = request.POST
                if 'silo' in params and not ag.granary.issilo(params['silo']):
                    # Create new silo
                    silo_name = params['silo']
                    g_root = config.get("granary.uri_root", "info:")
                    c.silo = ag.granary.get_rdf_silo(silo_name, uri_base="%s%s/datasets/" % (g_root, silo_name))
                    ag.granary._register_silos()
                    kw = {}
                    for term in accepted_params:
                        if term in params:
                            kw[term] = params[term]
                    du = ag.granary.disk_usage_silo(silo_name)
                    kw['disk_usage'] = du
                    ag.granary.describe_silo(silo_name, **kw)
                    ag.granary.sync()
                    # conneg return
                    accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                    if not accept_list:
                        accept_list= [MT("text", "html")]
                    mimetype = accept_list.pop(0)
                    while(mimetype):
                        if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                            redirect_to(controller="admin", action="index")
                        else:
                            response.status_int = 201
                            return "Created Silo %s" % silo_name
        else:
            abort(403)

    def archive(self, silo_name):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        c.granary_list = ag.granary.silos
        c.silo_name = silo_name
        # Admin only
        if ident.get('role') == "admin":
            http_method = request.environ['REQUEST_METHOD']
            if http_method == "GET":
                if ag.granary.issilo(silo_name):
                    c.kw = ag.granary.describe_silo(silo_name)
                    return render("/admin_siloview.html")
                else:
                    abort(404)
            elif http_method == "POST":
                params = request.POST
                if ag.granary.issilo(silo_name):
                    kw = {}
                    for term in accepted_params:
                        if term in params:
                            kw[term] = params[term]
                    ag.granary.describe_silo(silo_name, **kw)
                    ag.granary.sync()
                    # conneg return
                    accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                    if not accept_list:
                        accept_list= [MT("text", "html")]
                    mimetype = accept_list.pop(0)
                    while(mimetype):
                        if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                            c.message = "Metadata updated"
                            c.kw = ag.granary.describe_silo(silo_name)
                            return render("/admin_siloview.html")
                        else:
                            response.status_int = 204
                            return "Updated Silo %s" % silo_name
                else:
                    # Create new silo
                    g_root = config.get("granary.uri_root", "info:")
                    c.silo = ag.granary.get_rdf_silo(silo_name, uri_base="%s%s/" % (g_root, silo_name))
                    ag.granary._register_silos()
                    kw = {}
                    for term in accepted_params:
                        if term in params:
                            kw[term] = params[term]
                    ag.granary.describe_silo(silo_name, **kw)
                    ag.granary.sync()
                    response.status_int = 201
                    return "Created Silo %s" % silo_name
            elif http_method == "DELETE":
                if ag.granary.issilo(silo_name):
                    # Deletion of an entire Silo...
                    # Serious consequences follow this action
                    # Walk through all the items, emit a delete msg for each
                    # and then remove the silo
                    todelete_silo = ag.granary.get_rdf_silo(silo_name)
                    for item in todelete_silo.list_items():
                        ag.b.deletion(silo_name, item, ident=ident['repoze.who.userid'])
                    ag.granary.delete_silo(silo_name)
                    ag.b.silo_deletion(silo_name, ident=ident['repoze.who.userid'])
                    try:
                        del ag.granary.state[silo_name]
                    except:
                        pass
                    ag.granary.sync()
                    ag.granary._register_silos()
                    response.status_int = 200
                    return """{'status':'Silo %s deleted'}""" % silo_name
                else:
                    abort(404)
        else:
            abort(403)
        
