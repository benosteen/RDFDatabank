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

"""Setup the rdfdatabank application"""
import logging

from rdfdatabank.config.environment import load_environment
from rdfdatabank.model import meta, User, Group, Permission
from sqlalchemy.exc import IntegrityError

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup rdfdatabank here"""
    load_environment(conf.global_conf, conf.local_conf)
    log.info("Creating tables")
    meta.metadata.create_all(bind=meta.engine)
    log.info("Successfully setup")
 
    try:
        g0a = Group()
        g0a.group_name = u'databank_administrator'
        g0a.silo = u'*'
        meta.Session.add(g0a)
        """
        g1a = Group()
        g1a.group_name = u'sandbox_administrator'
        g1a.silo = u'sandbox'
        meta.Session.add(g1a)

        g1b = Group()
        g1b.group_name = u'sandbox_manager'
        g1b.silo = u'sandbox'
        meta.Session.add(g1b)

        g1c = Group()
        g1c.group_name = u'sandbox_submitter'
        g1c.silo = u'sandbox'
        meta.Session.add(g1c)

        g2a = Group()
        g2a.group_name = u'sandbox2_administrator'
        g2a.silo = u'sandbox2'
        meta.Session.add(g2a)

        g2b = Group()
        g2b.group_name = u'sandbox2_manager'
        g2b.silo = u'sandbox2'
        meta.Session.add(g2b)

        g2c = Group()
        g2c.group_name = u'sandbox2_submitter'
        g2c.silo = u'sandbox2'
        meta.Session.add(g2c)

        g3a = Group()
        g3a.group_name = u'sandbox3_administrator'
        g3a.silo = u'sandbox3'
        meta.Session.add(g3a)

        g3b = Group()
        g3b.group_name = u'sandbox3_manager'
        g3b.silo = u'sandbox3'
        meta.Session.add(g3b)

        g3c = Group()
        g3c.group_name = u'sandbox3_submitter'
        g3c.silo = u'sandbox3'
        meta.Session.add(g3c)
        """
        p1 = Permission()
        p1.permission_name = u'administrator'
        p1.groups.append(g0a)
        #p1.groups.append(g1a)
        #p1.groups.append(g2a)
        #p1.groups.append(g3a)
        meta.Session.add(p1)
 
        p2 = Permission()
        p2.permission_name = u'manager'
        #p2.groups.append(g1b)
        #p2.groups.append(g2b)
        #p2.groups.append(g3b)
        meta.Session.add(p2)
 
        p3 = Permission()
        p3.permission_name = u'submitter'
        #p3.groups.append(g1c)
        #p3.groups.append(g2c)
        #p3.groups.append(g3c)
        meta.Session.add(p3)
        """
        u0 = User()
        u0.user_name = u'admin'
        u0.name = u'Databank Administrator'
        u0._set_password(u'test')
        u0.groups.append(g0a)
        meta.Session.add(u0)
 
        u1 = User()
        u1.user_name = u'sandbox_user'
        u1.name = u'Test User I'
        u1._set_password(u'sandbox')
        u1.groups.append(g1c)
        meta.Session.add(u1) 

        u2 = User()
        u2.user_name = u'sandbox_user2'
        u2.name = u'Test User II'
        u2._set_password(u'sandbox2')
        u2.groups.append(g2c)
        meta.Session.add(u2) 

        u3 = User()
        u3.user_name = u'sandbox_user3'
        u3.name = u'Test User III'
        u3._set_password(u'sandbox3')
        u3.groups.append(g3c)
        meta.Session.add(u3) 

        u4 = User()
        u4.user_name = u'admin1'
        u4.name = u'Test Administrator I'
        u4._set_password(u'test')
        u4.groups.append(g1a)
        meta.Session.add(u4)
 
        u5 = User()
        u5.user_name = u'admin2'
        u5.name = u'Test Administrator II'
        u5._set_password(u'test2')
        u5.groups.append(g2a)
        meta.Session.add(u5)
 
        u6 = User()
        u6.user_name = u'admin3'
        u6.name = u'Test Administrator III'
        u6._set_password(u'test3')
        u6.groups.append(g3a)
        meta.Session.add(u6)
 
        u7 = User()
        u7.user_name = u'sandbox_manager'
        u7.name = u'Test Manager I'
        u7._set_password(u'managertest')
        u7.groups.append(g1b)
        meta.Session.add(u7)
 
        u8 = User()
        u8.user_name = u'sandbox_manager2'
        u8.name = u'Test Manager II'
        u8._set_password(u'managertest2')
        u8.groups.append(g2b)
        meta.Session.add(u8)
 
        u9 = User()
        u9.user_name = u'sandbox_manager3'
        u9.name = u'Test Manager III'
        u9._set_password(u'managertest3')
        u9.groups.append(g3b)
        meta.Session.add(u9)
        """
        meta.Session.flush()
        meta.Session.commit()
    except IntegrityError:
        log.error('there was a problem adding your auth data, it may have already been added. Continuing with bootstrapping...')
        #import traceback
        #print traceback.format_exc()
        meta.Session.rollback()
