# Frontend/Databank specific settings
try:
    from utils.namespaces import NAMESPACES, PREFIXES
except ImportError:
    pass

REDIS_HOST = 'localhost'

GRANARY_STORE = u'/tmp/silos'
GRANARY_URI_ROOT = u'http://databank/'

DOI_CONFIG = '/var/lib/databank/rdfdatabank/config/doi_config.py'
DOI_COUNT = '/var/lib/databank/rdfdatabank/config/doi_count'

BROADCAST_TO = u'redis'
BROADCAST_QUEUE = u'silochanges'

METADATA_EMBARGOED = False

SOLR_HOST = u'http://localhost:8080/solr'
NAMING_RULE = r'[^0-9a-zA-Z_\-\:]'
NAMING_RULE_HUMANIZED = u"numbers, letters, '-' and ':', must be more than one character long and must not contain any spaces."
FORMATS_SERVED = ('text/html',
                  'text/xhtml',
                  'text/plain',
                  'application/json',
                  'application/rdf+xml',
                  'text/xml',
                  'text/rdf+n3',
                  'application/x-turtle',
                  'text/rdf+ntriples',
                  'text/rdf+nt',
                  )
PUBLISHER = u'Bodleian Libraries, University of Oxford'
RIGHTS = 'http://ora.ouls.ox.ac.uk/objects/uuid%3A1d00eebb-8fed-46ad-8e38-45dbdb4b224c'
LICENSE = u'CC0 1.0 Universal (CC0 1.0). See http://creativecommons.org/publicdomain/zero/1.0/legalcode'
#license = Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. See http://creativecommons.org/licenses/by-nc-sa/3.0/

API_VERSION = 0.3

