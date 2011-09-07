# -*- coding: utf-8 -*-
"""The application's Globals object"""

from pylons import config

from recordsilo import Granary
from redis import Redis

from rdfdatabank.lib.utils import authz
from rdfdatabank.lib.htpasswd import HtpasswdFile
from rdfdatabank.lib.broadcast import BroadcastToRedis

from rdfdatabank.config.users import _USERS

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
        self.users = _USERS
       
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

        if config.has_key("metadata.embargoed"):
            self.metadata_embargoed = config['metadata.embargoed']
            if isinstance(self.metadata_embargoed, basestring):
                if self.metadata_embargoed.lower().strip() == 'true':
                    self.metadata_embargoed = True
                else:
                    self.metadata_embargoed = False
            elif not type(self.metadata_embargoed).__name__ == 'bool':
                self.metadata_embargoed = False
        else:
            self.metadata_embargoed = False

        if config.has_key("auth.file"):
            pwdfile = config['auth.file']
            self.passwdfile = HtpasswdFile(pwdfile)
            self.passwdfile.load()
         
        if config.has_key("auth.info"):
            self.userfile = config['auth.info']

        if config.has_key("doi.count"):
            self.doi_count_file = config['doi.count']
        
        if config.has_key("formats_served"):
            self.formats_served = config['formats_served']
        else:
            self.formats_served = ["text/html", "text/xhtml", "text/plain", "application/json", "application/rdf+xml", "text/xml"]

        if config.has_key("publisher"):
            self.publisher = config['publisher']
        else:
            self.publisher = "Bodleian Libraries, University of Oxford"

        if config.has_key("rights"):
            self.rights = config['rights']
      
        if config.has_key("license"):
            self.license = config['license']

