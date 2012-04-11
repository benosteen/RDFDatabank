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
import simplejson
import codecs
from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import rest
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
from rdfdatabank.lib.auth_entry import add_user, update_user, delete_user, add_group_users, delete_group_users
from rdfdatabank.lib.auth_entry import list_users, list_usernames, list_user_groups, list_group_users, list_user

#from rdfdatabank.config import users

log = logging.getLogger(__name__)

accepted_params = ['title', 'description', 'notes', 'owners', 'disk_allocation']

class UsersController(BaseController):
    @rest.restrict('GET', 'POST')
    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        if not ('administrator' in ident['permissions'] or 'manager' in ident['permissions']):
            abort(403, "Do not have administrator or manager credentials")

        c.ident = ident
        #granary_list = ag.granary.silos
        #silos = ag.authz(granary_list, ident, permission=['administrator', 'manager'])
        c.users = list_users()
        if 'administrator' in ident['permissions']:
            c.roles = ["admin", "manager", "user"]
        else:
            c.roles = ["manager", "user"]
        
        http_method = request.environ['REQUEST_METHOD']
        
        if http_method == "GET":
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
                    return render("/users.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(c.users)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/plain
            response.content_type = 'application/json; charset="UTF-8"'
            response.status_int = 200
            response.status = "200 OK"
            return simplejson.dumps(c.users)
        elif http_method == "POST":
            params = request.POST
            if not 'username' in params and not params['username']:
                abort(400, "username not supplied")
            existing_users = list_usernames()
            if params['username'] in existing_users:
                abort(403, "User exists")
            if (('firstname' in params and 'lastname' in params) or 'name' in params) and \
               'username' in params and params['username'] and 'password' in params and params['password']:
                add_user(params)
            else:   
                abort(400, "The following parameters have to be supplied: username, pasword and name (or firstname and lastanme)")
            response.status_int = 201
            response.status = "201 Created"
            response.headers['Content-Location'] = url(controller="users", action="userview", username=params['username'])
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
                    redirect(url(controller="users", action="userview", username=params['username']))
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
    def userview(self, username):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')

        http_method = request.environ['REQUEST_METHOD']        
        if http_method == 'GET' or 'DELETE':
            #Admins, managers and user can see user data / delete the user
            if not ('administrator' in ident['permissions'] or 'manager' in ident['permissions'] or ident['user'].user_name == username):
                abort(403, "Do not have administrator or manager credentials to view profiles of other users")
        elif http_method == 'POST':
            #Only user can updte their data
            if not ident['user'].user_name == username:
                abort(403, "Login as %s to edit profile"%username)

        c.ident = ident
        c.username = username

        if http_method == "GET":
            c.user = list_user(username)
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
                    return simplejson.dumps(c.user)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/html            
            response.content_type = 'application/json; charset="UTF-8"'
            response.status_int = 200
            response.status = "200 OK"
            return simplejson.dumps(c.user)
        elif http_method == "POST":
            params = request.POST
            update_user(params)
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
                    redirect(url(controller="users", action="userview", username=username))
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
        elif http_method == "DELETE":
            user_groups = list_user_groups(username)
            if user_groups:
                abort(403, "User is member of silos. Remove user from all silos before deleting them")
            #Deleet user from database
            delete_user(username)
            #TODO: Delete user from silos in database
            #TODO: Deleet user from silo description data
            #Get all the silos user belomgs to, remove them from each silo and sync silo metadata
            # conneg return
            accept_list = None
            response.content_type = "text/plain"
            response.status_int = 200
            response.status = "200 OK"
            return "{'ok':'true'}"

    @rest.restrict('GET')
    def siloview(self, silo):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        if not ag.granary.issilo(silo):
            abort(404)
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident, permission=['administrator', 'manager'])
        if not silo in silos:
            abort(403, "Do not have administrator or manager credentials for silo %s"%silo)
        user_groups = list_user_groups(ident['user'].user_name)
        if (silo, 'administrator') in user_groups:
            c.roles = ["admin", "manager", "user"]
        elif (silo, 'manager') in user_groups:
            c.roles = ["manager", "user"]
        else:
            #User is super user
            c.roles = ["admin", "manager", "user"]
        c.silo = silo
        
        http_method = request.environ['REQUEST_METHOD']
        
        if http_method == "GET":
            c.users = list_group_users(silo)
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
                    return render("/silo_users.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(c.users)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/plain
            response.content_type = 'application/json; charset="UTF-8"'
            response.status_int = 200
            response.status = "200 OK"
            return simplejson.dumps(c.users)

    @rest.restrict('GET', 'POST', 'DELETE')
    def silouserview(self, silo, username):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')

        granary_list = ag.granary.silos

        http_method = request.environ['REQUEST_METHOD']        
        if http_method == 'GET':
            silos = ag.authz(granary_list, ident)
            if not silo in silos:
                abort(403, "User is not a member of the silo %s"%silo)
            if not ('administrator' in ident['permissions'] or 'manager' in ident['permissions'] or ident['user'].user_name == username):
                abort(403, "Do not have administrator or manager credentials to view profiles of other users")
        else:
            silos = ag.authz(granary_list, ident, permission=['administrator', 'manager'])
            if not silo in silos:
                abort(403, "Do not have administrator or manager credentials for silo %s"%silo)
            if not ('administrator' in ident['permissions'] or 'manager' in ident['permissions']):
                abort(403, "Do not have administrator or manager credentials")

        c.ident = ident
        c.silo = silo
        c.username = username

        if http_method == "GET":
            c.user = list_user(username)
            if 'groups' in c.user and c.user['groups']:
                for i in c.user['groups']:
                    if i[0] != silo:
                        c.user['groups'].remove(i)
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
                    return render("/silo_user.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(c.user)
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/plain            
            response.content_type = 'application/json; charset="UTF-8"'
            response.status_int = 200
            response.status = "200 OK"
            return simplejson.dumps(c.user)
        elif http_method == "POST":
            params = request.POST
            if not ('role' in params and params['role'] and params['role'] in ['administrator', 'manager', 'submitter']):
                abort(400, "Parameters 'role' not found or is invalid")
            kw = ag.granary.describe_silo(silo)
            #Get existing owners, admins, managers and users
            owners = []
            admins = []
            managers = []
            submitters = []
            if 'owners' in kw and kw['owners']:
                owners = [x.strip() for x in kw['owners'].split(",") if x]
            if 'administrators' in kw and kw['administrators']:
                admins = [x.strip() for x in kw['administrators'].split(",") if x]
            if 'managers' in kw and kw['managers']:
                managers = [x.strip() for x in kw['managers'].split(",") if x]
            if 'submitters' in kw and kw['submitters']:
                submitters = [x.strip() for x in kw['submitters'].split(",") if x]
            to_remove = []
            to_add = []
            if params['role'] == 'administrator':
                if not username in admins:
                    to_add.append((username, 'administrator'))
                    admins.append(username)
                if not username in owners:
                    owners.append(username)
                if username in managers:
                    managers.remove(username)
                    to_remove.append((username, 'manager'))
                if username in submitters:
                    submitters.remove(username)
                    to_remove.append((username, 'submitter'))
            elif params['role'] == 'manager':
                if not username in managers:
                    to_add.append((username, 'manager'))
                    managers.append(username)
                if not username in owners:
                    owners.append(username)
                if username in admins:
                    if not 'administrator' in ident['permissions']:
                        abort(403, "Need to be admin to modify user of role admin")
                    if len(admins) == 1:
                        abort(403, "Add another administrator to silo before updating user role")
                    admins.remove(username)
                    to_remove.append((username, 'administrator'))
                if username in submitters:
                    submitters.remove(username)
                    to_remove.append((username, 'submitter'))
            elif params['role'] == 'submitter':
                if not username in submitters:
                    to_add.append((username, 'submitter'))
                    submitters.append(username)
                if not username in owners:
                    owners.append(username)
                if username in admins:
                    if not 'administrator' in ident['permissions']:
                        abort(403, "Need to be admin to modify user of role admin")
                    if len(admins) == 1:
                        abort(403, "Add another administrator to silo before updating user role")
                    admins.remove(username)
                    to_remove.append((username, 'administrator'))
                if username in managers:
                    if len(managers) == 1 and len(admins) == 0:
                        abort(403, "Add another administrator to silo before updating user role")
                    managers.remove(username)
                    to_remove.append((username, 'manager'))

            owners = list(set(owners))
            admins = list(set(admins))
            managers = list(set(managers))
            submitters = list(set(submitters))

            # Update silo info
            kw['owners'] = ','.join(owners)
            kw['administrators'] = ','.join(admins)
            kw['managers'] = ','.join(managers)
            kw['submitters'] = ','.join(submitters)
            ag.granary.describe_silo(silo, **kw)
            ag.granary.sync()

            #Add new silo users into database
            if to_add:
                add_group_users(silo, to_add)

            if to_remove:
                delete_group_users(silo, to_remove)

            #Set response code
            if not to_remove:
                response.status_int = 204
                response.status = "204 Updated"
                response_message = None
            elif to_add:
                response.status_int = 201
                response.status = "201 Created"
                response.headers['Content-Location'] = url(controller="users", action="silouserview", silo=silo, username=params['username'])
                response_message = "201 Created"
            else:
                response.status_int = 200
                response.status = "200 OK"
                response_message = "User role not updated"

            #Conneg return
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
                    redirect(url(controller="users", action="silouserview", silo=silo, username=username))
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    return response_message
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops nothing satisfies - return text/plain
            response.content_type = 'application/json; charset="UTF-8"'
            return response_message
        elif http_method == "DELETE":
            kw = ag.granary.describe_silo(silo)
            #Get existing owners, admins, managers and users
            owners = []
            admins = []
            managers = []
            submitters = []
            if 'owners' in kw and kw['owners']:
                owners = [x.strip() for x in kw['owners'].split(",") if x]
            if 'administrators' in kw and kw['administrators']:
                admins = [x.strip() for x in kw['administrators'].split(",") if x]
            if 'managers' in kw and kw['managers']:
                managers = [x.strip() for x in kw['managers'].split(",") if x]
            if 'submitters' in kw and kw['submitters']:
                submitters = [x.strip() for x in kw['submitters'].split(",") if x]

            #Gather user roles to delete
            to_remove = []
            if username in admins:
                if not 'administrator' in ident['permissions']:
                    abort(403, "Need to be admin to modify user of role admin")                
                if len(admins) == 1:
                    abort(403, "Add another administrator to silo before updating user role")
                to_remove.append((username, 'administrator'))
                admins.remove(username)
            if username in managers:
                managers.remove(username)
                to_remove.append((username, 'manager'))
            if username in submitters:
                submitters.remove(username)
                to_remove.append((username, 'submitter'))
            if username in owners:
                owners.remove(username)                

            owners = list(set(owners))
            admins = list(set(admins))
            managers = list(set(managers))
            submitters = list(set(submitters))

            if to_remove:
                # Update silo info
                kw['owners'] = ','.join(owners)
                kw['administrators'] = ','.join(admins)
                kw['managers'] = ','.join(managers)
                kw['submitters'] = ','.join(submitters)
                ag.granary.describe_silo(silo, **kw)
                ag.granary.sync()
                delete_group_users(silo, to_remove)
            else:
                abort(400, "No user to delete")
            accept_list = None
            response.content_type = "text/plain"
            response.status_int = 200
            response.status = "200 OK"
            return "{'ok':'true'}"

