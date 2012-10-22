from redis import Redis

from frontend.settings import REDIS_HOST, BROADCAST_TO, BROADCAST_QUEUE

from broadcast import BroadcastToRedis

r = Redis(REDIS_HOST)
b = BroadcastToRedis(REDIS_HOST, BROADCAST_QUEUE)
