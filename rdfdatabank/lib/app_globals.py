"""The application's Globals object"""

from pylons import config

from recordsilo import Granary
from redis import Redis

from rdfdatabank.lib.utils import authz
from rdfdatabank.lib.htpasswd import HtpasswdFile
from rdfdatabank.lib.broadcast import BroadcastToRedis

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
            
        if config.has_key("solr.host"):
            from solr import SolrConnection
            self.solrhost = config['solr.host']
            self.solr = SolrConnection(self.solrhost)
        
        if config.has_key("broadcast.to"):
            if config['broadcast.to'] == "redis":
                self.b = BroadcastToRedis(config['redis.host'], config['broadcast.queue'])

        if config.has_key("naming_rule"):
            self.naming_rule = config['naming_rule']

        self.passwdfile = HtpasswdFile(config['htpasswd.file'])
            pwdfile = self.granary.replace('silos', 'passwd')
            self.passwdfile.load(pwdfile)

