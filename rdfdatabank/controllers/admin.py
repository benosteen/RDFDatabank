import logging
import simplejson
from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import rest
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
from rdfdatabank.config import users

log = logging.getLogger(__name__)

accepted_params = ['title', 'description', 'notes', 'owners', 'disk_allocation']

class AdminController(BaseController):

    @rest.restrict('GET', 'POST')
    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.granary_list = ag.authz(granary_list, ident)
        
        if not ident.get('role') == "admin":
            abort(401, "Do not have admin credentials")

        # Admin only
        http_method = request.environ['REQUEST_METHOD']

        if http_method == "GET":
            #c.granary = ag.granary
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
                    return render("/silo_admin.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(list(c.granary_list))
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/html            
            return render("/silo_admin.html")
        elif http_method == "POST":
            params = request.POST
            if 'silo' in params:
                if ag.granary.issilo(params['silo']):
                    abort(403)
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
                        redirect_to(controller="admin", action="index")
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        response.status_int = 201
                        response.status = "201 Created"
                        response.headers['Content-Location'] = url(controller="silos", action="siloview", silo=silo_name)
                        return "201 Created Silo %s" % silo_name
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                # Whoops - nothing satisfies - return text/plain
                response.content_type = "text/plain"
                response.status_int = 201
                response.status = "201 Created"
                response.headers['Content-Location'] = url(controller="silos", action="siloview", silo=silo_name)
                return "201 Created Silo %s" % silo_name

    @rest.restrict('GET', 'POST', 'DELETE')
    def archive(self, silo_name):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        #c.granary_list = ag.granary.silos
        c.silo_name = silo_name
        # Admin only
        if not ident.get('role') == "admin":
            abort(401, "Do not have admin credentials")

        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if not silo_name in silos:
            abort(403)
        http_method = request.environ['REQUEST_METHOD']

        if http_method == "GET":
            if not ag.granary.issilo(silo_name):
                abort(404)
            c.kw = ag.granary.describe_silo(silo_name)
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
                    return render("/admin_siloview.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(dict(c.kw))
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/html            
            return render("/admin_siloview.html")
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
                        c.message = "Metadata updated"
                        c.kw = ag.granary.describe_silo(silo_name)
                        return render("/admin_siloview.html")
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        response.status_int = 204
                        response.status = "204 Updated"
                        #return "Updated Silo %s" % silo_name
                        return
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                # Whoops - nothing satisfies - return text/plain
                response.content_type = "text/plain"
                response.status_int = 204
                response.status = "204 Updated"
                return
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
                        redirect_to(controller="datasets", action="siloview", silo=silo_name)
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        response.status_int = 201
                        response.status = "201 Created"
                        response.headers['Content-Location'] = url(controller="datasets", action="siloview", silo=silo_name)
                        return "201 Created Silo %s" % silo_name
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                # Whoops - nothing satisfies - return text/plain
                response.content_type = "text/plain"
                response.status_int = 201
                response.status = "201 Created"
                response.headers['Content-Location'] = url(controller="datasets", action="siloview", silo=silo_name)
                return "201 Created Silo %s" % silo_name
        elif http_method == "DELETE":
            if not ag.granary.issilo(silo_name):
                abort(404)
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
                    redirect_to(controller="admin", action="index")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    response.status_int = 200
                    response.status = "200 OK"
                    return """{'status':'Silo %s deleted'}""" % silo_name
            # Whoops - nothing satisfies - return text/plain
            response.content_type = "text/plain"
            response.status_int = 200
            response.status = "200 OK"
            return """{'status':'Silo %s deleted'}""" % silo_name

    @rest.restrict('POST')
    def register(self, silo_name):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        #c.granary_list = ag.granary.silos
        c.silo_name = silo_name
        # Admin only
        if not ident.get('role') == "admin":
            abort(401, "Do not have admin credentials")
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if not silo_name in silos:
            abort(403)
        params = request.POST
        if 'owner' in params and params['owner'] and (('first_name' in params and 'last_name' in params) or 'name' in params) and \
           'username' in params and params['username'] and 'password' in params and params['password']:
            # Check if user id exists. Write new user into passwd file
            for entry in ag.passwdfile.entries:
                if entry[0] == params['username']:
                    code = 204
                else:
                    code = 201
            ag.passwdfile.update(params['username'], params['password'])
            ag.passwdfile.save()
            #Write user metadata and save the rdf file
            users._USERS[params['username']] = {'owner':params['owner'], 'role':'user'}
            if 'name' in params and params['name']:
                users._USERS[params['username']]['name'] = params['name']
            if 'first_name' in params and params['first_name']:
                users._USERS[params['username']]['first_name'] = params['first_name']
            if 'last_name' in params and params['last_name']:
                users._USERS[params['username']]['last_name'] = params['last_name']
            f = open(ag.userfile, 'w')
            f.write('_USERS = %s'%str(users._USERS))
            f.close()
            reload(users)
            silos_to_be_added = params['owner'].split(',')
            #Add owner to silos
            for s in silos_to_be_added:
                if not ag.granary.issilo(s):
                    continue
                c.kw = ag.granary.describe_silo(s)
                owners = c.kw.get('owners')
                if not params['username'] in owners:
                    owners = owners.strip().strip(',').strip()
                    owners = owners + ',%s'%params['username']
                    c.kw['owners'] = owners
                    ag.granary.describe_silo(silo_name, **c.kw)
                    ag.granary.sync()

            if code == 201:
                response.status_int = 201
                response.status = "201 Created"
                response.headers['Content-Location'] = url(controller="admin", action="archive", silo_name=silo_name)
                response_message = "201 Created"
            if code == 204:
                response.status_int = 204
                response.status = "204 Updated"
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
                    redirect_to(controller="admin", action="archive", silo_name=silo_name)
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
