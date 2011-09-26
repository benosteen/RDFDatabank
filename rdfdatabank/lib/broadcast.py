# -*- coding: utf-8 -*-
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

