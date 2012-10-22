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

#from rdfdatabank.model import meta, User, Group, Permission, Datasets
#from sqlalchemy.exc import IntegrityError
#import traceback

import logging
log = logging.getLogger(__name__)

from django.contrib.auth.models import User, Group

from frontend.models import Dataset, Silo

from django.db import transaction

ROLES =    (u'superuser',
            u'administrator',
            u'manager',
            u'submitter',
           )

def add_auth_info_to_context(request, c):
    c.current_path = request.path
    if request.user.is_authenticated():
        c.is_logged_in = True
        c.username = request.user.username
        c.user_logged_in = {}
        c.user_logged_in['permissions'] = [r for s,r in list_user_group_and_permissions(request.user.username)]

def group_name(siloname, role):
    # FIXME: Assumes siloname and role aren't complex strings
    # Failing edge cases are possible
    if role == u"superuser":
        return u"superuser"
    return u"%s.%s" % (siloname, role)

def silo_role_from_group(group_name):
    # FIXME: Assumes siloname and role aren't complex strings
    # Failing edge cases are possible
    if group_name == u"superuser":
        return (None, u"superuser")
    s = group_name.rsplit(".", 1)
    if len(s) == 2:
        return s
    else:
        log.error("FATAL: Group name '%s' was not parsable into silo and role" % group_name)
        return

def add_group_helper(siloname, role):
    gname = group_name(siloname, role)
    try:
        group = Group.objects.get(name=gname)
        log.info("Skipping '%s' - exists in db already" % group_name)
    except Group.DoesNotExist:
        log.info("Creating '%s'")
        g = Group(name=gname)
        g.save()

def del_group_helper(siloname, role):
    group_name = group_name(siloname, role)
    try:
        group = Group.objects.get(name=group_name)
        log.info("Deleting '%s'")
        g.delete()
    except Group.DoesNotExist:
        log.info("Skipping '%s' - does not exists in db" % group_name)

@transaction.commit_on_success
def add_silo(siloname):    
    if siloname == "*":
        # make sure superuser role exists
        add_group_helper(None, u"superuser")
        return True
    
    s, status = Silo.objects.get_or_create(silo=siloname)
    if status:
        log.info("Added Silo: '%s'" % siloname)
    else:
        log.info("Silo '%s' already in db" % siloname)
    
    for role in ROLES[1:]:             #skip superuser
        # Make sure role exists for a given group
        add_group_helper(siloname, role)
    
    return True

@transaction.commit_on_success
def delete_silo(silo_name):
    if silo_name == '*':
        del_group_helper(None, u"superuser")
    else:
        Group.objects.filter(name__startswith=silo_name).delete()
        #for role in ROLES[1:]:
        #    del_group_helper(siloname, role)
    return True

@transaction.commit_on_success
def add_user(user_details):
    # Does user already exist?
    try:
        u = User.objects.get(username=user_details['username'])
        log.warn("Username '%s' already exists. Not overwriting." % user_details['username'])
        return False
    except User.DoesNotExist:
        # parameter cleanup
        username=user_details['username'][:30]
        name = user_details.get('name', '')[:70]
        first_name = user_details.get('firstname', '')[:30]
        last_name = user_details.get('lastname', '')[:30]
        email = user_details.get('email','')[:40]
        u = User(username=username, 
                 first_name=first_name,
                 last_name=last_name,
                 email=email )

        u.set_password(user_details.get('password', ''))
        if user_details.get('password', '') == '':
            u.set_unusable_password()
            log.warn("User: '%s' hasn't supplied a usable password. Marking as such.'")

        u.save()
        # (Create and) set the name in the profile to the one supplied
        u.profile.name = name
        u.profile.save()
        u.save()
        
    return True

@transaction.commit_on_success
def update_user(user_details):
    if not ('username' in user_details and user_details['username']):
        return False
    try:
        u = User.objects.get(username=user_details['username'])
        log.info("Updating user '%s'" % user_details['username'])
        if 'password' in user_details and user_details['password']:
            u.set_password(user_details['password'])

        if 'name' in user_details and user_details['name']:
            u.profile.name = u'%s'%user_details['name'][:70]
            u.profile.save()

        if 'firstname' in user_details and user_details['firstname']:
            u.first_name = u'%s'%user_details['firstname'][:30]

        if 'lastname' in user_details and user_details['lastname']:
            u.last_name = u'%s'%user_details['lastname'][:30]

        if 'email' in user_details and user_details['email']:
            u.email = u'%s'%user_details['email'][:70]

        u.save()
    except User.DoesNotExist:
        log.error("User '%s' doesn't exist in db. Cannot update.'" % user_details['username'])
        return False
    return True

@transaction.commit_on_success
def delete_user(username):
    try:
        u = User.objects.get(username=username)
        log.info("Deleting user '%s'" % username)
        u.profile.delete()
        u.delete()
    except User.DoesNotExist:
        log.error('Error deleting user %s. Does the user exist?' % username)
        return False
    return True

@transaction.commit_on_success
def add_user_groups(username, groups):
    #groups is a list of (silo_name, permission_name) tuples
    try:
        groups_list_names = [group_name(*group) for group in groups]
        u = User.objects.get(username=username)
        log.info("Adding user '%s' to %s" % (username, groups_list_names))
        # gather list of group objects
        groups_list = []
        for gname in groups_list_names:
            try:
                if gname == u"superuser":
                    # Create this group, if it doesn't exist
                    g_obj = Group.objects.get_or_create(name=gname)
                else:
                    g_obj = Group.objects.get(name=gname)
                groups_list.append(g_obj)
            except Group.DoesNotExist:
                log.warn("Group '%s' does not exist so cannot add '%s' to it" % (gname, username))
                # TODO: Should groups be automagically added here?
                return False
                
        u.groups.add(*groups_list)
        u.save()
    except User.DoesNotExist:
        log.error('Error finding user %s to update permissions. Does the user exist?'%username)
        return False
    return True

@transaction.commit_on_success
def delete_user_groups(username, groups):
    #groups is a list of (silo_name, permission_name) tuples
    try:
        groups_list_names = [group_name(*group) for group in groups]
        u = User.objects.get(username=username)
        log.info("Adding user '%s' to %s" % (username, groups_list_names))
        # gather list of group objects
        groups_list = []
        for gname in groups_list_names:
            try:
                g_obj = Group.objects.get(name=gname)
                groups_list.append(g_obj)
            except Group.DoesNotExist:
                log.warn("Group '%s' does not exist so cannot add '%s' to it" % (gname, username))
                # TODO: Should groups be automagically added here?
                return False
                
        u.groups.remove(*groups_list)
        u.save()
    except User.DoesNotExist:
        log.error('Error finding user %s to update permissions. Does the user exist?'%username)
        return False
    return True

@transaction.commit_on_success
def add_group_users(silo_name, user_groups):
    #user_groups is a list of (user_name, permission_name) tuples
    groups_holder = {}
    user_holder = {}
    user_groups_holder = {}
    for user, role in user_groups:
        if not user_groups_holder.has_key(user):
            user_groups_holder[user] = []
        try:
            gname = group_name(silo_name, role)
            if not groups_holder.has_key(gname):
                g_obj = Group.objects.get(name=gname)
                groups_holder[gname] = g_obj
                user_groups_holder[user].append(g_obj)
            else:
                user_groups_holder[user].append(groups_holder[gname])
        except Group.DoesNotExist:
            log.warn("Group '%s' does not exist" % (gname))
            # TODO: Should groups be automagically added here?
            return False
        
        try:
            if not user_holder.has_key(user):
                u_obj = User.objects.get(username=user)
                user_holder[user] = u_obj
        except User.DoesNotExist:
            log.warn("User '%s' does not exist" % (user))
            # TODO: Should users be automagically added here?
    
    # Now actually add the users to their groups
    for user, roles in user_groups_holder.iteritems():
        user_holder[user].groups.add(*roles)
        user_holder[user].save()
    
    # explicitly delete references to the heavy db object collections
    # to give the gc a headstart
    del groups_holder
    del user_holder
    del user_groups
    
    return True

@transaction.commit_on_success
def delete_group_users(silo_name, user_groups):    
    #user_groups is a list of (user_name, permission_name) tuples
    groups_holder = {}
    user_holder = {}
    user_groups_holder = {}
    for user, role in user_groups:
        if not user_groups_holder.has_key(user):
            user_groups_holder[user] = []
        try:
            gname = group_name(silo_name, role)
            if not groups_holder.has_key(gname):
                g_obj = Group.objects.get(name=gname)
                groups_holder[gname] = g_obj
                user_groups_holder[user].append(g_obj)
            else:
                user_groups_holder[user].append(groups_holder[gname])
        except Group.DoesNotExist:
            log.warn("Group '%s' does not exist" % (gname))
            # TODO: Should groups be automagically added here?
            return False
        
        try:
            if not user_holder.has_key(user):
                u_obj = User.objects.get(username=user)
                user_holder[user] = u_obj
        except User.DoesNotExist:
            log.warn("User '%s' does not exist" % (user))
            # TODO: Should users be automagically added here?
    
    # Now actually add the users to their groups
    for user, roles in user_groups_holder.iteritems():
        user_holder[user].groups.remove(*roles)
        user_holder[user].save()
    
    # explicitly delete references to the heavy db object collections
    # to give the gc a headstart
    del groups_holder
    del user_holder
    del user_groups
    
    return True

def list_user_details(username, user_object=None):
    try:
        u = user_object
        if u == None:
            u = User.objects.get(username=username)
            log.info("Getting user '%s' information" % username)
        
        user_details = {}
        user_details['user_name'] = u.username
        user_details['name'] = u.profile.name
        user_details['firstname'] = u.first_name
        user_details['lastname'] = u.last_name
        user_details['email'] = u.email
        user_details['groups'] = []
        # groups user belongs to
        for g in u.groups.iterator():
            user_details['groups'].append((silo_role_from_group(g.name)))
        return user_details
        
    except User.DoesNotExist:
        log.error("Error getting user '%s' information. Does the user exist?" % username)
        return {}

def list_users():
    users_list = []
    for user in User.objects.iterator():
        users_list.append(list_user_details(None, user))     # pass User db object instead of username
    return users_list

def list_groups():
    #groups = meta.Session.query(Group)
    #for g in groups:
    #    print g.id, g.group_name, g.silo
    #    permissions associated with the group
    #    for p in g.permissions:
    #        print p.id, p.permission_name
    
    # FIXME Hmm, leaky db access here (db implementation in controller/view code someplace)
    return [g.name for g in Group.objects.all()]

def list_silos(star=False):
    return [s.silo for s in Silo.objects.iterator() if star == False and s.silo != "*"]

def list_permissions():
    return ROLES

def list_usernames():
    return [u.username for u in User.objects.iterator()]

def list_user_group_and_permissions(username, siloname=None):
    try:
        u = User.objects.get(username=username)
        if siloname != None:
            group_list = u.groups.filter(name__startswith=siloname)
        else:
            group_list = u.groups.all()
        roles = []
        for g in group_list:
            silo, role = silo_role_from_group(g.name)
            roles.append((silo, role))
        return roles
    except User.DoesNotExist:
        log.error('Error getting user %s. Does the user exist?' % username)
        return False

def list_user_permissions(username, siloname):
    permission_list = list_user_group_and_permissions(username, siloname)
    if permission_list:
        return [r for s,r in permission_list]
    else:
        return []
    
def list_user_groups(username):
    permission_list = list_user_group_and_permissions(username)
    return permission_list

def list_group_users(siloname):
    # NOTE: Original code seems to have oddness wrt users with multiple
    # permissions for a single silo.
    # New code mimics this until I can see why
    # would be better if 'permission' key in returned dict was
    # a list of permissions?
    
    group_users =[]
    for u in User.objects.filter(groups__name__startswith=siloname):
        details = {'user_name':u.username,
                   'name':u.profile.name,
                   'firstname':u.first_name,
                   'lastname':u.last_name,
                   'email':u.email}
        for group in u.groups.filter(name__startswith=siloname):
            silo, role = silo_role_from_group(group.name)
            record = {'permission': role}
            record.update(details)
            group_users.append(record)
    
    return group_users

def list_group_usernames(siloname):
    admins = []
    managers = []
    submitters = []
    
    for u in User.objects.filter(groups__name__startswith=siloname):
        for group in u.groups.filter(name__startswith=siloname):
            silo, role = silo_role_from_group(group.name)
            username = u.username
            if role == 'administrator' and not username in admins:
                admins.append(username)
            if role == 'manager' and not username in managers:
                managers.append(username)
            if role == 'submitter' and not username in submitters:
                submitters.append(username)
    return (admins, managers, submitters)

def list_new_users():
    # Expensive operation...
    #Users not a part of any group
    
    ungrouped_users =[]
    for u in User.objects.all():
        if u.groups.count() == 0:
            ungrouped_users.append({
                'user_name':u.username,
                'permission':None,
                'name':u.profile.name,
                'firstname':u.first_name,
                'lastname':u.last_name})
    
    return ungrouped_users

def list_user(username):
    try:
        u = User.objects.get(username=username)
        user_details = {}
        user_details['id'] = u.id     # is this necessary?
        user_details['user_name'] = u.username
        user_details['name'] = u.profile.name
        user_details['firstname'] = u.first_name
        user_details['lastname'] = u.last_name
        user_details['email'] = u.email
        user_details['groups'] = list_user_group_and_permissions(username)
        return user_details
    except User.DoesNotExist:
        log.error('Error geting user %s info. Does the user exist?' % username)
        return False

@transaction.commit_on_success
def add_dataset(silo_name, id, name=None):
    # Unhappy about mixing db access modes here - ORM or is direct id needed for some reason?
    silo, status = Silo.objects.get_or_create(silo=silo_name)
    if status:
        log.warn("Needed to instantiate Silo '%s' in the database" % silo_name)
        add_silo(silo_name)
    d, status = Dataset.objects.get_or_create(id = id, silo = silo)
    if name != None:
        d.name = name
    d.save()
    return status

@transaction.commit_on_success
def delete_dataset(silo_name, id):
    try:
        d = Dataset.objects.get(id = id)
        d.delete()
        return True
    except Dataset.DoesNotExist:
        log.error('Error deleting dataset %s in silo %s'%(id, silo_name))
        return False
    return True

def get_datasets_count(silo_name):
    d_count = Dataset.objects.filter(silo__silo__exact=silo_name).count()
    return d_count

def get_datasets(silo_name, start=0, rows=100):
    # NOTE: Pagination I guess?
    try:
        start = int(start)
    except:
        start = 0
    try:
        rows = int(rows)
    except:
        rows = 100
    
    return [d.id for d in Dataset.objects.filter(silo__silo__exact=silo_name)[start:rows+start]]

def is_superuser(username):
    try:
        if User.objects.get(username=username).groups.filter(name__exact=u"superuser").count() >= 1:
            return True
    except User.DoesNotExist:
        log.error("User %s doesn't exist" % username)
    return False

def authz(ident, permission=[]):
    silos=[]
    roles=ROLES
    if permission != []:
        if type(permission).__name__ != "list":
            roles = [permission]
        else:
            roles = permission
    permission_list = list_user_groups(ident.username)
    if permission_list:
        for silo, role in permission_list:
            if silo == None and role == u'superuser':
                # superuser - return full list
                return list_silos()
            elif role in roles:
                silos.append(silo)
        return silos
    else:
        return []

