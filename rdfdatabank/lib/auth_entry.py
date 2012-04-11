from rdfdatabank.model import meta, User, Group, Permission
from sqlalchemy.exc import IntegrityError

def add_silo(silo_name):
    try:
        p_q = meta.Session.query(Permission)

        ga = Group()
        ga.group_name = u'%s_administrator'%silo_name
        ga.silo = u"%s"%silo_name
        meta.Session.add(ga)

        p_q_admin = p_q.filter(Permission.permission_name == u'administrator').one()
        p_q_admin.groups.append(ga)

        gb = Group()
        gb.group_name = u'%s_manager'%silo_name
        gb.silo = u"%s"%silo_name
        meta.Session.add(gb)

        p_q_manager = p_q.filter(Permission.permission_name == u'manager').one()
        p_q_manager.groups.append(gb)

        gc = Group()
        gc.group_name = u'%s_submitter'%silo_name
        gc.silo = u'%s'%silo_name
        meta.Session.add(gc)

        p_q_submitter = p_q.filter(Permission.permission_name == u'submitter').one()
        p_q_submitter.groups.append(gc)

        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding silo data, it may have already been added'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def delete_silo(silo_name):
    try:
        g_q = meta.Session.query(Group)
        g_q_group1 = g_q.filter(Group.group_name == u'%s_administrator'%silo_name).one()
        g_q_group2 = g_q.filter(Group.group_name == u'%s_manager'%silo_name).one()
        g_q_group3 = g_q.filter(Group.group_name == u'%s_submitter'%silo_name).one()
        meta.Session.delete(g_q_group1)
        meta.Session.delete(g_q_group2)
        meta.Session.delete(g_q_group3)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem deleting silo data, it may have already been deleted'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def add_user(user_details):
    u = User()
    u.user_name = user_details['username']
    u._set_password(u'%s'%user_details['password'])

    if 'name' in user_details and user_details['name']:
        u.name = u'%s'%user_details['name']

    if 'firstname' in user_details and user_details['firstname']:
        u.firstname = u'%s'%user_details['firstname']

    if 'lastname' in user_details and user_details['lastname']:
        u.lastname = u'%s'%user_details['lastname']

    if 'email' in user_details and user_details['email']:
        u.email = u'%s'%user_details['email']
    try:
        meta.Session.add(u)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding user data. The user may have already been added'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def update_user(user_details):
    if not ('username' in user_details and user_details['username']):
        return False
    try:
        u_q = meta.Session.query(User)
        u = u_q.filter(User.user_name == u'%s'%user_details['username']).one()

        if 'password' in user_details and user_details['password']:
            u._set_password(u'%s'%user_details['password'])

        if 'name' in user_details and user_details['name']:
            u.name = u'%s'%user_details['name']

        if 'firstname' in user_details and user_details['firstname']:
            u.firstname = u'%s'%user_details['firstname']

        if 'lastname' in user_details and user_details['lastname']:
            u.lastname = u'%s'%user_details['lastname']

        if 'email' in user_details and user_details['email']:
            u.email = u'%s'%user_details['email']

        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem updating user data. Does the user exist?'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def delete_user(username):
    try:
        u_q = meta.Session.query(User)
        u = u_q.filter(User.user_name == u'%s'%username).one()
        meta.Session.delete(u)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem deleting user data. Does the user exist?'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def add_user_groups(username, groups):
    #groups is a list of (silo_name, permission_name) tuples
    try:
        u_q = meta.Session.query(User)
        u = u_q.filter(User.user_name == u'%s'%username).one()
        g_q = meta.Session.query(Group)
        for silo_name, permission_name in groups:
            g_q_group = g_q.filter(Group.group_name == u'%s_%s'%(silo_name, permission_name)).one()
            u.groups.append(g_q_group)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding user to group. Does the user and group exist?'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def delete_user_groups(username, groups): 
    #groups is a list of (silo_name, permission_name) tuples
    try:
        u_q = meta.Session.query(User)
        u = u_q.filter(User.user_name == u'%s'%username).one()
        g_q = meta.Session.query(Group)
        for silo_name, permission_name in groups:
            g = g_q.filter(Group.group_name == u'%s_%s'%(silo_name, permission_name)).one()
            query = "DELETE FROM user_group WHERE user_id=%d and group_id=%d"%(u.id, g.id)
            meta.Session.execute(query)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem deleting user from group. Does the user and group exist and is the user a member of the group?'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def add_group_users(silo_name, user_groups):
    #user_groups is a list of (user_name, permission_name) tuples
    try:
        u_q = meta.Session.query(User)
        g_q = meta.Session.query(Group)
        for username, permission_name in user_groups:
            u = u_q.filter(User.user_name == u'%s'%username).one()
            if u:
                g_q_group = g_q.filter(Group.group_name == u'%s_%s'%(silo_name, permission_name)).one()
                u.groups.append(g_q_group)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding users to group. Does the user and group exist?'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def delete_group_users(silo_name, user_groups):
    #user_groups is a list of (user_name, permission_name) tuples
    try:
        u_q = meta.Session.query(User)
        g_q = meta.Session.query(Group)
        for username, permission_name in user_groups:
            u = u_q.filter(User.user_name == u'%s'%username).one()
            g = g_q.filter(Group.group_name == u'%s_%s'%(silo_name, permission_name)).one()
            query = "DELETE FROM user_group WHERE user_id=%d and group_id=%d"%(u.id, g.id)
            meta.Session.execute(query)
        meta.Session.commit()
    except IntegrityError:
        print 'Warning, there was a problem deleting users from group. Does the user and group exist and is the user a member of the group?'
        import traceback
        print traceback.format_exc()
        meta.Session.rollback()
    return True

def list_users():
    users = meta.Session.query(User)
    users_list = []
    for u in users:
        # print u.id, u.user_name, u.email, u.name, u.firstname, u.lastname
        # u._get_password
        user_details = {}
        user_details['user_name'] = u.user_name
        user_details['name'] = u.name
        user_details['firstname'] = u.firstname
        user_details['lastname'] = u.lastname
        user_details['email'] = u.email
        user_details['groups'] = []
        # groups user belongs to
        for g in u.groups:
            # print g.id, g.group_name, g.silo
            # permissions associated with the group
            for p in g.permissions:
                # print p.id, p.permission_name
                user_details['groups'].append((g.silo, p.permission_name))
        users_list.append(user_details)
    return users_list

def list_groups():
    groups = meta.Session.query(Group)
    #for g in groups:
    #    print g.id, g.group_name, g.silo
    #    permissions associated with the group
    #    for p in g.permissions:
    #        print p.id, p.permission_name
    return groups

def list_silos(star=False):
    silos = []
    groups = meta.Session.query(Group)
    for g in groups:
        if g.silo == "*" and star and not g.silo in silos:
            silos.append(g.silo)
        elif not g.silo in silos and g.silo != "*":
            silos.append(g.silo)
    return silos

def list_permissions():
    permissions = meta.Session.query(Permission)
    #for p in permissions:
    #    print p.id, p.permission_name
    return permissions

def list_usernames():
    users = meta.Session.query(User)
    usernames = []
    for u in users:
        usernames.append(u.user_name)
    return usernames

def list_user_permissions(username, siloname):
    u_q = meta.Session.query(User)
    u = u_q.filter(User.user_name == u'%s'%username).one()
    p_list = []
    #groups user belongs to
    for g in u.groups:
        if g.silo == siloname:
            #permissions associated with the group
            for p in g.permissions:
                p_list.append(p.permission_name)
    return p_list

def list_user_groups(username):
    u_q = meta.Session.query(User)
    u = u_q.filter(User.user_name == u'%s'%username).one()
    groups =[]
    for g in u.groups:
        for p in g.permissions:
            groups.append((g.silo, p.permission_name))
    return groups

def list_group_users(siloname):
    all_users = meta.Session.query(User)
    group_users =[]
    for u in all_users:
        for g in u.groups:
            if g.silo == siloname:
                #permissions associated with the group
                for p in g.permissions:
                    group_users.append({
                        'user_name':u.user_name,
                        'permission':p.permission_name,
                        'name':u.name,
                        'firstname':u.firstname,
                        'lastname':u.lastname})
    return group_users

def list_new_users():
    #Users not a part of any group
    all_users = meta.Session.query(User)
    ungrouped_users =[]
    for u in all_users:
        if not u.groups:
            ungrouped_users.append({
                'user_name':u.user_name,
                'permission':None,
                'name':u.name,
                'firstname':u.firstname,
                'lastname':u.lastname})
    return ungrouped_users

def list_user(username):
    u_q = meta.Session.query(User)
    u = u_q.filter(User.user_name == u'%s'%username).one()
    user_details = {}
    user_details['id'] = u.id
    user_details['user_name'] = u.user_name
    user_details['name'] = u.name
    user_details['firstname'] = u.firstname
    user_details['lastname'] = u.lastname
    user_details['email'] = u.email
    user_details['groups'] = []
    for g in u.groups:
        for p in g.permissions:
            user_details['groups'].append((g.silo, p.permission_name))
    return user_details
