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
 
"""Intended to work like a quick-started SQLAlchemy plugin"""
 
from repoze.what.middleware import AuthorizationMetadata
from repoze.what.plugins.pylonshq import booleanize_predicates
from repoze.what.plugins.sql import configure_sql_adapters
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin
from repoze.who.plugins.sa import SQLAlchemyUserMDPlugin

from rdfdatabank.model import meta, User, Group, Permission

# authenticator plugin
authenticator = SQLAlchemyAuthenticatorPlugin(User, meta.Session)
#authenticator.translations['user_name'] = 'username'

# metadata provider plugins
#
# From the documentation in repoze.what.plugins.sql.adapters package
#
# For developers to be able to use the names they want in their model, both the
# groups and permissions source adapters use a "translation table" for the
# field and table names involved:
#  * Group source adapter:
#    * "section_name" (default: "group_name"): The name of the table field that
#      contains the primary key in the groups table.
#    * "sections" (default: "groups"): The groups to which a given user belongs.
#    * "item_name" (default: "user_name"): The name of the table field that
#      contains the primary key in the users table.
#    * "items" (default: "users"): The users that belong to a given group.
#  * Permission source adapter:
#    * "section_name" (default: "permission_name"): The name of the table field
#      that contains the primary key in the permissions table.
#    * "sections" (default: "permissions"): The permissions granted to a given
#      group.
#    * "item_name" (default: "group_name"): The name of the table field that
#      contains the primary key in the groups table.
#    * "items" (default: "groups"): The groups that are granted a given
#      permission.

#adapters = configure_sql_adapters(User, Group, Permission, meta.Session,
#                                  group_translations={'section_name': 'name',
#                                                      'item_name': 'username'},
#                                  permission_translations={'section_name': 'name',
#                                                           'item_name': 'username'})
adapters = configure_sql_adapters(User, Group, Permission, meta.Session)

user = SQLAlchemyUserMDPlugin(User, meta.Session)
#user.translations['user_name'] = 'username'

group = AuthorizationMetadata(
    {'sqlauth': adapters['group']}, 
    {'sqlauth': adapters['permission']}
)

# THIS IS CRITICALLY IMPORTANT!  Without this your site will
# consider every repoze.what predicate True!
booleanize_predicates()

