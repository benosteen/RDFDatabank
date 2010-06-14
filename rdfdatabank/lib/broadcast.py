from redis import Redis
from redis.exceptions import ConnectionError

class BroadcastToRedis(object):
    def __init__(self, redis_host, queue):
        self.redis_host = redis_host
        self.queue = queue
        self.r = Redis(redis_host)
        
    def lpush(self, msg):
        try:
            self.r.lpush(self.queue, msg)
        except ConnectionError:
            self.r = Redis(self.redis_host)
            self.lpush(self.queue, msg)
        
    def b_change(self, silo, id, filepath=None, **kw):
        msg = {}
        msg.update(kw)
        msg.update({'type':'u',
                   'silo':silo,
                   'id':id})
        if filepath:
                msg['filepath'] = filepath
        self.lpush(simplejson.dumps(msg))
        
    def b_creation(self, silo, id, filepath=None, *kw):
        msg = {}
        msg.update(kw)
        msg.update({'type':'c',
                   'silo':silo,
                   'id':id})
        if filepath:
                msg['filepath'] = filepath
        self.lpush(simplejson.dumps(msg))

    def b_deletion(self, silo, id, filepath=None, **kw):
        msg = {}
        msg.update(kw)
        msg.update({'type':'d',
                   'silo':silo,
                   'id':id})
        if filepath:
                msg['filepath'] = filepath
        self.lpush(simplejson.dumps(msg))

