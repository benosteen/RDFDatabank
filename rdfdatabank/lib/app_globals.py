"""The application's Globals object"""

from pylons import config

from recordsilo import Granary
from redis import Redis

from rdfdatabank.lib.utils import authz

class Globals(object):

    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        
        self.authz = authz
        
        if config.has_key("granary.store"):
            self.granary = Granary(config['granary.store'])
            
        if config.has_key("redis.host"):
            self.redishost = config['redis.host']
            self.r = Redis(self.redishost)
