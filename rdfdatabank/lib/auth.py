# coding: utf-8
 
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

