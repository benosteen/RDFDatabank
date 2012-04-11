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

from redis import Redis
from redis.exceptions import ConnectionError

import simplejson

from datetime import datetime

class BroadcastToRedis(object):
    def __init__(self, redis_host, queue):
        self.redis_host = redis_host
        self.queue = queue
        self.r = Redis(redis_host)
        
    def lpush(self, msg):
        try:
            self.r.lpush(self.queue, msg)
        except ConnectionError:  # The client can sometimes be timed out and disconnected at the server.
            self.r = Redis(self.redis_host)
            self.r.lpush(self.queue, msg)
        
    def change(self, silo, id, filepath=None, **kw):
        msg = {}
        msg.update(kw)
        msg['_timestamp'] = datetime.now().isoformat()
        msg.update({'type':'u',
                   'silo':silo,
                   'id':id})
        if filepath:
                msg['filepath'] = filepath
        self.lpush(simplejson.dumps(msg))
        
    def creation(self, silo, id, filepath=None, **kw):
        msg = {}
        msg.update(kw)
        msg['_timestamp'] = datetime.now().isoformat()
        msg.update({'type':'c',
                   'silo':silo,
                   'id':id})
        if filepath:
                msg['filepath'] = filepath
        self.lpush(simplejson.dumps(msg))

    def deletion(self, silo, id, filepath=None, **kw):
        msg = {}
        msg.update(kw)
        msg['_timestamp'] = datetime.now().isoformat()
        msg.update({'type':'d',
                   'silo':silo,
                   'id':id})
        if filepath:
                msg['filepath'] = filepath
        self.lpush(simplejson.dumps(msg))

    def silo_deletion(self, silo, **kw):
        msg = {}
        msg.update(kw)
        msg['_timestamp'] = datetime.now().isoformat()
        msg.update({'type':'d',
                   'silo':silo})
        self.lpush(simplejson.dumps(msg))

    def embargo_change(self, silo, id, embargoed=None, until=None, **kw):
        msg = {}
        msg.update(kw)
        msg['_timestamp'] = datetime.now().isoformat()
        msg.update({'type':'embargo',
                   'silo':silo,
                   'id':id,
                   'embargoed':embargoed,
                   'embargoed_until':until})
        self.lpush(simplejson.dumps(msg))

