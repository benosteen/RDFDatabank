#-*- coding: utf-8 -*-
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
from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import rest
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
from rdfdatabank.lib.auth_entry import add_silo, delete_silo, add_group_users, delete_group_users
from rdfdatabank.lib.auth_entry import add_user, update_user, list_usernames, list_user_groups
import codecs

log = logging.getLogger(__name__)

accepted_params = ['title', 'description', 'notes', 'owners', 'disk_allocation', 'administrators', 'managers', 'submitters']

class AdminController(BaseController):

    @rest.restrict('GET', 'POST')
    def index(self):
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        granary_list = ag.granary.silos
        c.granary_list = ag.authz(granary_list, ident, permission=['administrator', 'manager'])

        http_method = request.environ['REQUEST_METHOD']

        if http_method == 'GET':
            if not 'administrator' in ident['permissions'] and not 'manager' in ident['permissions']:
                abort(403, "Do not have administrator or manager credentials")
        else:
            if not 'administrator' in ident['permissions']:
                abort(403, "Do not have administrator credentials")

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
                    return render("/admin_silos.html")
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
            return render("admin_silos.html")
        elif http_method == "POST":
            params = request.POST
            if 'silo' in params:
                if ag.granary.issilo(params['silo']):
                    abort(403, "The silo %s exists"%params['silo'])
                #NOTE:
                #If any userid in params['administrators']/params['managers']/params['submitters'] does not exist, return 403
                #if administartor list is empty, append current user to administartor list
                #Owner is the superset of adminstrators, managers and submitters
                existing_users = list_usernames()
                owners = []
                admins = []
                managers = []
                submitters = []
                #if 'owners' in params and params['owners']:
                #    owners = [x.strip() for x in kw['owners'].split(",") if x]
                if 'administrators' in params and params['administrators']:
                    admins = [x.strip() for x in params['administrators'].split(",") if x]
                    owners.extend(admins)
                if 'managers' in params and params['managers']:
                    managers = [x.strip() for x in params['managers'].split(",") if x]
                    owners.extend(managers)
                if 'submitters' in params and params['submitters']:
                    submitters = [x.strip() for x in params['submitters'].split(",") if x]
                    owners.extend(submitters)
                if not admins:
                    owners.append(ident['user'].user_name)
                    admins.append(ident['user'].user_name)
                owners = list(set(owners))
                for o in owners:
                    if not o in existing_users:
                        abort (403, "User %s does not exist"%o)
                admins = list(set(admins))
                managers = list(set(managers))
                submitters = list(set(submitters))

                # Create new silo
                silo = params['silo']
                g_root = config.get("granary.uri_root", "info:")
                c.silo = ag.granary.get_rdf_silo(silo, uri_base="%s%s/datasets/" % (g_root, silo))
                ag.granary._register_silos()
                kw = {}
                for term in accepted_params:
                    if term in params:
                        kw[term] = params[term]       
                kw['owners'] = ','.join(owners)
                kw['administrators'] = ','.join(admins)
                kw['managers'] = ','.join(managers)
                kw['submitters'] = ','.join(submitters)
                du = ag.granary.disk_usage_silo(silo)
                kw['disk_usage'] = du
                ag.granary.describe_silo(silo, **kw)
                ag.granary.sync()

                # Add silo to database
                add_silo(silo)
                
                #Add users belonging to the silo, to the database
                all_silo_users = []
                
                for a in admins:
                    all_silo_users.append((a, 'administrator'))
                for a in managers:
                    all_silo_users.append((a, 'manager'))
                for a in submitters:
                    all_silo_users.append((a, 'submitter'))
                add_group_users(params['silo'], all_silo_users)
 
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
                        redirect(url(controller="silos", action="siloview", silo=silo))
                    elif str(mimetype).lower() in ["text/plain", "application/json"]:
                        response.content_type = "text/plain"
                        response.status_int = 201
                        response.status = "201 Created"
                        response.headers['Content-Location'] = url(controller="silos", action="siloview", silo=silo)
                        return "201 Created Silo %s" % silo
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                # Whoops - nothing satisfies - return text/plain
                response.content_type = "text/plain"
                response.status_int = 201
                response.status = "201 Created"
                response.headers['Content-Location'] = url(controller="silos", action="siloview", silo=silo)
                return "201 Created Silo %s" % silo
            else:
                response.content_type = "text/plain"
                response.status_int = 400
                response.status = "400 Bad Request"
                return "400 Bad request.  No valid parameters found."

    @rest.restrict('GET', 'POST', 'DELETE')
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
        if ('*', 'administrator') in user_groups:
            #User is super user
            c.roles = ["admin", "manager", "user"]
        elif (silo, 'administrator') in user_groups:
            c.roles = ["admin", "manager", "user"]
        elif (silo, 'manager') in user_groups:
            c.roles = ["manager", "user"]
        else:
            abort(403, "Do not have administrator or manager credentials for silo %s"%silo)
        http_method = request.environ['REQUEST_METHOD']

        c.kw = ag.granary.describe_silo(silo)
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
            #Get existing owners, admins, managers and submitters
            owners = []
            admins = []
            managers = []
            submitters = []
            if 'owners' in c.kw and c.kw['owners']:
                owners = [x.strip() for x in c.kw['owners'].split(",") if x]
            if 'administrators' in c.kw and c.kw['administrators']:
                admins = [x.strip() for x in c.kw['administrators'].split(",") if x]
            if 'managers' in c.kw and c.kw['managers']:
                managers = [x.strip() for x in c.kw['managers'].split(",") if x]
            if 'submitters' in c.kw and c.kw['submitters']:
                submitters = [x.strip() for x in c.kw['submitters'].split(",") if x]

            #Get new members
            new_owners = []
            #Get new admins
            new_admins = []
            if 'administrators' in params and params['administrators']:
                returned_admins = [x.strip() for x in params['administrators'].split(",") if x]
                new_admins = [x for x in returned_admins if not x in admins]
                new_owners.extend(new_admins)
            #Get new managers
            new_managers = []
            if 'managers' in params and params['managers']:
                returned_managers = [x.strip() for x in params['managers'].split(",") if x]
                new_managers = [x for x in returned_managers if not x in managers]
                new_owners.extend(new_managers)
            #Get new submitters
            new_submitters = []
            if 'submitters' in params and params['submitters']:
                returned_submitters = [x.strip() for x in params['submitters'].split(",") if x]
                new_submitters = [x for x in returned_submitters if not x in submitters]
                new_owners.extend(new_submitters)

            #Check if the new members exist. If not return 403
            existing_users = list_usernames()
            new_owners = list(set(new_owners))
            for o in new_owners:
                if not o in existing_users:
                    abort (403, "User %s does not exist"%o)

            if new_admins and not 'admin' in c.roles:
                abort (403, "Only administrators can assing users to role 'administrator'")

            owners.extend(new_owners)
            new_admins = list(set(new_admins))
            admins.extend(new_admins)
            new_managers = list(set(new_managers))
            managers.extend(new_managers)
            new_submitters = list(set(new_submitters))
            submitters.extend(new_submitters)

            # Update silo info
            updateMetadata = False
            for term in accepted_params:
                if term in params and not term in ['owners', 'administrators', 'managers', 'submitters'] and params[term]:
                    c.kw[term] = params[term]
                    updateMetadata = True 
            if new_owners or new_admins or new_managers or new_submitters or updateMetadata:
                new_silo_users = []
                if new_owners:
                    c.kw['owners'] = ','.join(owners)
                if new_admins:
                    c.kw['administrators'] = ','.join(admins)
                    for a in new_admins:
                        new_silo_users.append((a, 'administrator'))
                if new_managers:
                    c.kw['managers'] = ','.join(managers)
                    for a in new_managers:   
                        new_silo_users.append((a, 'manager'))
                if new_submitters:
                    c.kw['submitters'] = ','.join(submitters)
                    for a in new_submitters:
                        new_silo_users.append((a, 'submitter'))
                #Add metadat changes to the silo
                ag.granary.describe_silo(silo, **c.kw)
                ag.granary.sync()
                #Add new silo users into database
                if new_silo_users:
                    add_group_users(silo, new_silo_users)
                       
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
                    c.kw = ag.granary.describe_silo(silo)
                    return render("/admin_siloview.html")
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = "text/plain"
                    response.status_int = 204
                    response.status = "204 Updated"
                    #return "Updated Silo %s" % silo
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
        elif http_method == "DELETE":
            # Deletion of an entire Silo...
            # Serious consequences follow this action
            # Walk through all the items, emit a delete msg for each
            # and then remove the silo
            todelete_silo = ag.granary.get_rdf_silo(silo)
            for item in todelete_silo.list_items():
                try:
                    ag.b.deletion(silo_name, item, ident=ident['repoze.who.userid'])
                except:
                    pass
            ag.granary.delete_silo(silo)
            try:
                ag.b.silo_deletion(silo_name, ident=ident['repoze.who.userid'])
            except:
                pass
            try:
                del ag.granary.state[silo]
            except:
                pass
            ag.granary.sync()
            ag.granary._register_silos()
            #Delete silo from database
            delete_silo(silo)
            # conneg return
            accept_list = None
            response.content_type = "text/plain"
            response.status_int = 200
            response.status = "200 OK"
            return "{'ok':'true'}"
    """
    @rest.restrict('POST')
    def register(self, silo):
        #Add user
        if not request.environ.get('repoze.who.identity'):
            abort(401, "Not Authorised")
        if not ag.granary.issilo(silo):
            abort(404)
        ident = request.environ.get('repoze.who.identity')
        c.ident = ident
        c.silo = silo
        # Admin only
        granary_list = ag.granary.silos
        silos = ag.authz(granary_list, ident, permission=['administrator', 'manager'])
        if not silo in silos:
            abort(403, "Do not have administrator or manager credentials for silo %s"%silo)
        params = request.POST
        if not ('username' in params and params['username']):
            abort(400, "username not supplied")
        existing_users = list_usernames()
        if params['username'] in existing_users:
            ug = list_user_groups(params['username'])
            if not ((params['username'], 'administrator') in ug or (params['username'], 'manager') in ug or (params['username'], 'submitter') in ug):
                abort(403, "User %s is not a part of the silo %s"%(params['username'], silo))
            code = 204
        else:
            code = 201
        owner_of_silos = []
        if code == 201:
            #Can only add user details. User membershipis managed through each silo
            if (('first_name' in params and 'last_name' in params) or 'name' in params) and \
               'username' in params and params['username'] and 'password' in params and params['password']:
                add_user(params)
            else:
                abort(400, "The following parameters have to be supplied: username, pasword and name (or firstname and lastanme)")
            response.status_int = 201
            response.status = "201 Created"
            response.headers['Content-Location'] = url(controller="admin", action="siloview", silo=silo)
            response_message = "201 Created"
        if code == 204:
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
                redirect(url(controller="admin", action="siloview", silo=silo))
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
    """
