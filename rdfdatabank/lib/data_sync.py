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

from rdfdatabank.lib.auth_entry import list_silos, list_usernames, list_group_usernames, add_silo, add_group_users

def sync_members(g):
    # NOTE: g._register_silos() IS AN EXPENSIVE OPERATION.
    # THIS FUNCTION IS EXPENSIVE AND SHOULD BE CALLED ONLY IF REALLY NECESSARY
    #g = ag.granary
    g.state.revert()
    g._register_silos()
    granary_list = g.silos

    granary_list_database = list_silos()
    usernames = list_usernames()
    for silo in granary_list:
        if not silo in granary_list_database:
            add_silo(silo)
        kw = g.describe_silo(silo)

        #Get existing owners, admins, managers and submitters from silo metadata
        owners = []
        admins = []
        managers = []
        submitters = []
        if 'administrators' in kw and kw['administrators']:
            admins = [x.strip() for x in kw['administrators'].split(",") if x]
        if 'managers' in kw and kw['managers']:
            managers = [x.strip() for x in kw['managers'].split(",") if x]
        if 'submitters' in kw and kw['submitters']:
            submitters = [x.strip() for x in kw['submitters'].split(",") if x]

        # Check users in silo metadata are valid users
        owners = [x for x in owners if x in usernames]
        admins = [x for x in admins if x in usernames]
        managers = [x for x in managers if x in usernames]
        submitters = [x for x in submitters if x in usernames]

        #Synchronize members in silo metadata with users in database 
        d_admins = []
        d_managers = []
        d_sunbmitters = []
        if silo in granary_list_database:
            d_admins, d_managers, d_submitters = list_group_usernames(silo)
            admins.extend(d_admins)
            managers.extend(d_managers)
            submitters.extend(d_submitters)

        # Ensure users are listed just once in silo metadata and owner is superset
        owners.extend(admins)
        owners.extend(managers)
        owners.extend(submitters)        
        admins = list(set(admins))
        managers = list(set(managers))
        submitters = list(set(submitters))
        owners = list(set(owners))

        # Add users in silo metadata to the database
        new_silo_users = []
        for a in admins:
            if not a in d_admins:
                new_silo_users.append((a, 'administrator'))           
        for a in managers:
            if not a in d_managers:
                new_silo_users.append((a, 'manager'))
        for a in new_submitters:
            if not a in d_submitters:
                new_silo_users.append((a, 'submitter'))
        if new_silo_users:
            add_group_users(silo, new_silo_users)

        #Write members into silo 
        kw['owners'] = ','.join(owners)
        kw['administrators'] = ','.join(admins)
        kw['managers'] = ','.join(managers)
        kw['submitters'] = ','.join(submitters)
        g.describe_silo(silo, **kw)
 
    g.sync()
    return
