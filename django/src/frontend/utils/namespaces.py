from rdflib import Namespace

NAMESPACES = {}
NAMESPACES['rdf'] = Namespace(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
NAMESPACES['rdfs'] = Namespace(u'http://www.w3.org/2000/01/rdf-schema#')
NAMESPACES['dc'] = Namespace(u'http://purl.org/dc/elements/1.1/')
NAMESPACES['dcterms'] = Namespace(u'http://purl.org/dc/terms/')
NAMESPACES['foaf'] = Namespace(u'http://xmlns.com/foaf/0.1/')
NAMESPACES['oxds'] = Namespace(u'http://vocab.ox.ac.uk/dataset/schema#')
NAMESPACES['ore'] = Namespace(u'http://www.openarchives.org/ore/terms/')
NAMESPACES['bibo'] = Namespace(u'http://purl.org/ontology/bibo/')

PREFIXES = {}
PREFIXES['http://www.w3.org/1999/02/22-rdf-syntax-ns#'] = 'rdf'
PREFIXES['http://www.w3.org/2000/01/rdf-schema#'] = 'rdfs'
PREFIXES['http://purl.org/dc/elements/1.1/'] = 'dc'
PREFIXES['http://purl.org/dc/terms/'] = 'dcterms'
PREFIXES['http://xmlns.com/foaf/0.1/'] = 'foaf'
PREFIXES['http://vocab.ox.ac.uk/dataset/schema#'] = 'oxds'
PREFIXES['http://www.openarchives.org/ore/terms/'] = 'ore'
PREFIXES['http://purl.org/ontology/bibo/'] = 'bibo'


