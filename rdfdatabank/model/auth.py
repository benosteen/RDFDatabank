# -*- coding: utf-8 -*-
"""
SQLAlchemy-powered model definitions for repoze.what SQL plugin.
Sets up Users, Groups and Permissions
"""

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer
from sqlalchemy.orm import relation
from rdfdatabank.model.meta import metadata, Base
import os
from hashlib import sha1

__all__ = ['User', 'Group', 'Permission']

# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('silo.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('user.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('group_id', Integer, ForeignKey('silo.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

class Group(Base):
    """
    Group definition for :mod:`repoze.what`.
 
    Only the ``group_name`` column is required by :mod:`repoze.what`.
 
    """
 
    __tablename__ = 'silo'
 
    # columns
 
    id = Column(Integer, autoincrement=True, primary_key=True)
    group_name = Column(Unicode(255), unique=True, nullable=False)
    silo = Column(Unicode(255))
 
    # relations
 
    users = relation('User', secondary=user_group_table, backref='groups')
 
    # special methods
 
    #def __repr__(self):
    #    return '<Group: name=%r>' % self.group_name
 
    #def __unicode__(self):
    #    return self.group_name

class Permission(Base):
    """
    Permission definition for :mod:`repoze.what`.
 
    Only the ``permission_name`` column is required by :mod:`repoze.what`.
 
    """
 
    __tablename__ = 'permission'
 
    # columns
 
    id = Column(Integer, autoincrement=True, primary_key=True)
    permission_name = Column(Unicode(255), unique=True, nullable=False)
 
    # relations
 
    groups = relation(Group, secondary=group_permission_table, backref='permissions')
 
    # special methods
 
    #def __repr__(self):
    #    return '<Permission: name=%r>' % self.permission_name
 
    #def __unicode__(self):
    #    return self.permission_name

class User(Base):

    """
    User definition.
 
    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``user_name`` column.
 
    """
    __tablename__ = 'user'

    #column

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_name = Column(Unicode(255), unique=True, nullable=False)
    password = Column(Unicode(80), nullable=False)
    email = Column(Unicode(255))
    name = Column(Unicode(255))
    firstname = Column(Unicode(255))
    lastname = Column(Unicode(255))

    def _set_password(self, password):
        """Hash password on the fly."""
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        # Make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode
        # fields
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        self.password = hashed_password

    def _get_password(self):
        """Return the password hashed"""
        return self.password

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hashed_pass = sha1()
        hashed_pass.update(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()
    
    def permissions(self):
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    #def __repr__(self):
    #    return '<User: name=%r, email=%r>' % (self.name, self.email)
 
    #def __unicode__(self):
    #    return self.name

