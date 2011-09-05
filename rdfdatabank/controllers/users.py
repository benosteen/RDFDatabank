import logging
import simplejson
from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import rest
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
#from rdfdatabank.config import users

log = logging.getLogger(__name__)

accepted_params = ['title', 'description', 'notes', 'owners', 'disk_allocation']

class UsersController(BaseController):
    @rest.restrict('GET', 'POST')
    def index(self, silo_name):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        c.silo_name = silo_name

        if not ag.granary.issilo(silo_name):
            abort(404)

        # Admin only
        if not ident.get('role') in ["admin", "manager"]:
            abort(403, "User does not have admin credentials")
      
        if ident.get('role') == "admin":
            c.roles = ["admin", "manager", "user"]
        else:
            c.roles = ["manager", "user"]

        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if not silo_name in silos:
            abort(403, "User does not have access to the silo")
 
        http_method = request.environ['REQUEST_METHOD']

        if http_method == "GET":
            if not ag.granary.issilo(silo_name):
                abort(404)
            kw = ag.granary.describe_silo(silo_name)
            c.users = []
            if 'owners' in kw.keys() and kw['owners']:
                c.users =  [x.strip() for x in kw['owners'].split(",") if x]
            for u in c.users:
                if not u in ag.users:
                    c.users.remove(u)
                if ag.users[u]['role'] == "admin" and ident.get('role') == "manager":
                    c.users.remove(u)
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
                    return render("/admin_users.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(c.users)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/html            
            return render("/admin_users.html")
        elif http_method == "POST":
            params = request.POST
            if not 'username' in params and not params['username']:
                abort(400, "username not supplied")
            if params['username'] in ag.users:
                abort(403, "User exists")
            code = 201
            owner_of_silos = []
            if 'owner' in params and params['owner'] and (('first_name' in params and 'last_name' in params) or 'name' in params) and \
               'username' in params and params['username'] and 'password' in params and params['password']:
                ag.passwdfile.update(params['username'], params['password'])
                ag.passwdfile.save()
                if 'role' in params and params['role'] and params['role'] in ['admin', 'manager', 'user']:
                    ag.users[params['username']]['role'] = params['role']
                else:
                    ag.users[params['username']]['role'] = 'user'
                owner_of_silos = params['owner'].strip().split(',')
                for s in owner_of_silos:
                    if s == '*' and ag.users[params['username']]['role'] == 'admin':
                        continue
                    if s and not ag.granary.issilo(s):
                        owner_of_silos.remove(s)
                ag.users[params['username']] = {'owner':owner_of_silos}
                if 'name' in params and params['name']:
                    ag.users[params['username']]['name'] = params['name']
                if 'first_name' in params and params['first_name']:
                    ag.users[params['username']]['first_name'] = params['first_name']
                if 'last_name' in params and params['last_name']:
                    ag.users[params['username']]['last_name'] = params['last_name']
            else:   
                abort(400, " No valid parameters found")

            f = open(ag.userfile, 'w')
            f.write('_USERS = %s'%str(ag.users))
            f.close()
            #reload(users)
            #silos_to_be_added = ag.users[params['username']]['owner']
            #Add owner to silos
            if owner_of_silos:
                for s in owner_of_silos:
                    if not ag.granary.issilo(s):
                        continue
                    c.kw = ag.granary.describe_silo(s)
                    owners = c.kw.get('owners')
                    if owners and not type(owners).__name__ == 'list':
                        owners = owners.split(',')
                    if not params['username'] in owners:
                        #owners = owners.strip().strip(',').strip()
                        owners.append(params['username'])
                        owners = ','.join(owners)
                        c.kw['owners'] = owners
                        ag.granary.describe_silo(silo_name, **c.kw)
                        ag.granary.sync()
            response.status_int = 201
            response.status = "201 Created"
            response.headers['Content-Location'] = url(controller="users", action="userview", \
                                             silo_name=silo_name, username=params['username'])
            response_message = "201 Created"

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
                    redirect_to(controller="users", action="userview", silo_name=silo_name, username=params['username'])
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

    @rest.restrict('GET', 'POST', 'DELETE')
    def userview(self, silo_name, username):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        c.silo_name = silo_name
        c.username = username
        if not ag.granary.issilo(silo_name):
            abort(404)

        # Admin only
        if not ident.get('role') in ["admin", "manager"]:
            abort(403, "User does not have admin credentials")
        if ident.get('role') == "admin":
            c.roles = ["admin", "manager", "user"]
        else:
            c.roles = ["manager", "user"]

        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident)
        if not silo_name in silos:
            abort(403, "User does not have access to the silo")

        http_method = request.environ['REQUEST_METHOD']

        if http_method == "GET":
            if not username in ag.users:
                abort(404)
            #if ag.users[username]['role'] == "admin" and ident.get('role') == "manager":
            #    abort(403)
            c.user =  ag.users[username]
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
                    return render("/admin_user.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(dict(c.user))
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/html            
            return render("/admin_user.html")
        elif http_method == "POST":
            params = request.POST
            if not username:
                abort(400, "username not supplied")
            if username in ag.users:
                existing_owners_of_silo = []
                kw = ag.granary.describe_silo(silo_name)
                if "owners" in kw.keys():
                    existing_owners_of_silo = [x.strip() for x in kw['owners'].split(",") if x]
                if not username in existing_owners_of_silo:
                    abort(403, "User not a part of the silo")
                if ag.users[username]['role'] == "admin" and ident.get('role') == "manager":
                    abort(403, "Manager cannot update admin user")
                code = 204
            else:
                code = 201
            owner_of_silos = []
            if code == 201:            
                if 'owner' in params and params['owner'] and 'password' in params and params['password'] and \
                    (('first_name' in params and 'last_name' in params) or 'name' in params):
                    ag.passwdfile.update(username, params['password'])
                    ag.passwdfile.save()
                    if 'role' in params and params['role'] and params['role'] in c.roles:
                        ag.users[username]['role'] = params['role']
                    else:
                        ag.users[username]['role'] = 'user'
                    owner_of_silos = params['owner'].strip().split(',')
                    for s in owner_of_silos:
                        if s == '*' and ag.users[username]['role'] == 'admin':
                            continue
                        if s and not ag.granary.issilo(s):
                            owner_of_silos.remove(s)
                    ag.users[username] = {'owner':owner_of_silos}
                    if 'name' in params and params['name']:
                        ag.users[username]['name'] = params['name']
                    if 'first_name' in params and params['first_name']:
                        ag.users[username]['first_name'] = params['first_name']
                    if 'last_name' in params and params['last_name']:
                        ag.users[username]['last_name'] = params['last_name']
            if code == 204:
                if 'password' in params and params['password']:
                    ag.passwdfile.update(username, params['password'])
                    ag.passwdfile.save()
                if 'role' in params and params['role'] and params['role'] in c.roles:
                    ag.users[username]['role'] = params['role']
                if 'owner' in params and params['owner']:
                    owner_of_silos = params['owner'].strip().split(',')
                    for s in owner_of_silos:
                        if  s == '*' and ag.users[username]['role'] == 'admin':
                            continue
                        if not ag.granary.issilo(s):
                            owner_of_silos.remove(s)
                    ag.users[username]['owner'] = owner_of_silos
                if 'name' in params and params['name']:
                    ag.users[username]['name'] = params['name']
                if 'first_name' in params and params['first_name']:
                    ag.users[username]['first_name'] = params['first_name']
                if 'last_name' in params and params['last_name']:
                    ag.users[username]['last_name'] = params['last_name']

            f = open(ag.userfile, 'w')
            f.write('_USERS = %s'%str(ag.users))
            f.close()
            #reload(users)
            #silos_to_be_added = ag.users[params['username']]['owner']
            #Add owner to silos
            if owner_of_silos:
                for s in owner_of_silos:
                    if not ag.granary.issilo(s):
                        continue
                    c.kw = ag.granary.describe_silo(s)
                    owners = c.kw.get('owners')
                    if owners and not type(owners).__name__ == 'list':
                        owners = owners.split(',')
                    if not username in owners:
                        #owners = owners.strip().strip(',').strip()
                        owners.append(username)
                        owners = ','.join(owners)
                        c.kw['owners'] = owners
                        ag.granary.describe_silo(silo_name, **c.kw)
                        ag.granary.sync()
            if code == 201:
                response.status_int = 201
                response.status = "201 Created"
                response.headers['Content-Location'] = url(controller="users", action="userview", \
                                                       silo_name=silo_name, username=username)
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
                    redirect_to(controller="users", action="userview", silo_name=silo_name, username=username)
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
