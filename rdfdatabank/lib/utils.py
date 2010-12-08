from datetime import datetime, timedelta

from redis import Redis
import simplejson

from pylons import app_globals as ag

from rdflib import ConjunctiveGraph
from rdflib import StringInputSource
from rdflib import Namespace, RDF, RDFS, URIRef

from uuid import uuid4
import re

ID_PATTERN = re.compile(r"^[0-9A-z\-\:]+$")

def authz(granary_list,ident):
    g = ag.granary
    g.state.revert()
    g._register_silos()
    granary_list = g.silos
    def _parse_owners(silo_name):
        kw = g.describe_silo(silo_name)
        if "owners" in kw.keys():
            owners = [x.strip() for x in kw['owners'].split(",") if x]
            return owners
        else:
            return []
    
    if ident['role'] == "admin":
        return granary_list
    else:
        authd = []
        for item in granary_list:
            owners = _parse_owners(item)
            if ident['repoze.who.userid'] in owners:
                authd.append(item)
        return authd

def allowable_id(identifier):
    if ID_PATTERN.match(identifier):
        return identifier

def allowable_id2(strg):
    if len(strg) < 2 or ' ' in strg:
        return False
    search=re.compile(r'%s'%ag.naming_rule).search
    return not bool(search(strg))

def is_embargoed(silo, id, refresh=False):
    # TODO evaluate r.expire settings for these keys - popularity resets ttl or increases it?
    r = Redis()
    e = r.get("%s:%s:embargoed" % (silo.state['storage_dir'], id))
    e_d = r.get("%s:%s:embargoed_until" % (silo.state['storage_dir'], id))
    if refresh or (not e or not e_d):
        if silo.exists(id):
            item = silo.get_item(id)
            e = item.metadata.get("embargoed")
            e_d = item.metadata.get("embargoed_until")
            if e not in ['false', 0, False]:
                e = True
            else:
                e = False
            r.set("%s:%s:embargoed" % (silo.state['storage_dir'], id), e)
            r.set("%s:%s:embargoed_until" % (silo.state['storage_dir'], id), e_d)
    return (e, e_d)

def create_new(silo, id, creator, title=None, embargoed=True, embargoed_until=None, embargo_days_from_now=None, **kw):
    item = silo.get_item(id)
    item.metadata['createdby'] = creator
    item.metadata['embargoed'] = embargoed
    item.metadata['uuid'] = uuid4().hex
    item.add_namespace('oxds', "http://vocab.ox.ac.uk/dataset/schema#")
    item.add_triple(item.uri, u"rdf:type", "oxds:DataSet")

    if embargoed:
        if embargoed_until:
            embargoed_until_date = embargoed_until
        elif embargo_days_from_now:
            embargoed_until_date = (datetime.now() + timedelta(days=embargo_days_from_now)).isoformat()
        else:
            embargoed_until_date = (datetime.now() + timedelta(days=365*70)).isoformat()
        item.metadata['embargoed_until'] = embargoed_until_date
        item.add_triple(item.uri, u"oxds:isEmbargoed", 'True')
        item.add_triple(item.uri, u"oxds:embargoedUntil", embargoed_until_date)
    else:
        item.add_triple(item.uri, u"oxds:isEmbargoed", 'False')
    item.add_triple(item.uri, u"dcterms:identifier", id)
    item.add_triple(item.uri, u"dcterms:creator", creator)   
    item.add_triple(item.uri, u"dcterms:created", datetime.now())
    item.add_triple(item.uri, u"oxds:currentVersion", item.currentversion)
    
    #TODO: Add current version metadata
    if title:
        item.add_triple(item.uri, u"rdfs:label", title)
    item.sync()
    return item

def get_readme_text(item, filename="README"):
    with item.get_stream(filename) as fn:
        text = fn.read().decode("utf-8")
    return u"%s\n\n%s" % (filename, text)

def test_rdf(text):
    g = ConjunctiveGraph()
    try:
        g = g.parse(StringInputSource(text), format='xml')
        return True
    except:
        return False

def munge_manifest(manifest_str, item, manifest_type='http://vocab.ox.ac.uk/dataset/schema#Grouping'):    
    #Get triples from the manifest file and remove the file
    triples = None
    ns = None
    seeAlsoFiles = None
    ns, triples, seeAlsoFiles = read_manifest(item, manifest_str, manifest_type=manifest_type)
    if ns and triples:
        for k, v in ns.iteritems():
            item.add_namespace(k, v)
        for (s, p, o) in triples:
            if str(p) == 'http://purl.org/dc/terms/title':
                item.del_triple(item.uri, u"dcterms:title")    
            item.add_triple(s, p, o)
    item.sync()
    if seeAlsoFiles:
        for fileuri in seeAlsoFiles:
            fullfilepath = None
            filepath = fileuri.replace(item.uri, '').strip().lstrip('/')
            fullfilepath = item.to_dirpath(filepath=filepath)
            if fullfilepath and item.isfile(fullfilepath):
                with item.get_stream(filepath) as fn:
                    text = fn.read()
                if test_rdf(text):
                    munge_manifest(text, item, manifest_type=manifest_type)
    return True

def read_manifest(item, manifest_str, manifest_type='http://vocab.ox.ac.uk/dataset/schema#Grouping'):
    triples = []
    namespaces = {}
    seeAlsoFiles = []
    oxdsClasses = ['http://vocab.ox.ac.uk/dataset/schema#Grouping', 'http://vocab.ox.ac.uk/dataset/schema#DataSet']

    aggregates = item.list_rdf_objects(item.uri, "ore:aggregates")
    
    g = ConjunctiveGraph()
    gparsed = g.parse(StringInputSource(manifest_str), format='xml')
    namespaces = dict(g.namespaces())
    
    #Get the subjects
    #subjects = {}
    #for s in gparsed.subjects():
    #    if s in subjects:
    #        continue
    #    if type(s).__name__ == 'BNode' or (type(s).__name__ == 'URIRef' and len(s) == 0):
    #        subjects[s] = item.uri
    #    else:
    #        for o in aggregates:
    #            if str(s) in str(o):
    #                subjects[s] = o
    #                break
    #        if not s in subjects:
    #            subjects[s] = s

    #Get the dataset type
    datasetType = False
    for s,p,o in gparsed.triples((None, RDF.type, None)):
        if str(o) == manifest_type:
            datasetType = True
            if type(s).__name__ == 'URIRef' and len(s) > 0 and str(s) != str(item.uri):
                namespaces['owl'] = URIRef("http://www.w3.org/2002/07/owl#")
                triples.append((item.uri, 'owl:sameAs', s))
                triples.append((item.uri, RDF.type, URIRef(manifest_type)))    
        elif str(o) in oxdsClasses and type(s).__name__ == 'URIRef' and str(s) == str(item.uri):
            gparsed.remove((s, p, o))

    #Get the uri for the see also files
    for s,p,o in gparsed.triples((None, URIRef('http://www.w3.org/2000/01/rdf-schema#seeAlso'), None)):
        for objs in aggregates:
            if str(o) in str(objs):
                seeAlsoFiles.append(str(objs))
        gparsed.remove((s, p, o))

    #Add remaining triples
    for s,p,o in gparsed.triples((None, None, None)):
        if datasetType or type(s).__name__ == 'BNode' or (type(s).__name__ == 'URIRef' and len(s) == 0):
            triples.append((item.uri, p, o))
        else:
            triples.append((s, p, o))
    return namespaces, triples, seeAlsoFiles

def manifest_type(manifest_str):
    mani_types = []
    g = ConjunctiveGraph()
    gparsed = g.parse(StringInputSource(manifest_str), format='xml')
    for s,p,o in gparsed.triples((None, RDF.type, None)):
        mani_types.append(str(o))
    if "http://vocab.ox.ac.uk/dataset/schema#DataSet" in mani_types:
        return "http://vocab.ox.ac.uk/dataset/schema#DataSet"
    elif "http://vocab.ox.ac.uk/dataset/schema#Grouping" in mani_types:
        return "http://vocab.ox.ac.uk/dataset/schema#Grouping"
    return None

def serialisable_stat(stat):
    stat_values = {}
    for f in ['st_atime', 'st_blksize', 'st_blocks', 'st_ctime', 'st_dev', 'st_gid', 'st_ino', 'st_mode', 'st_mtime', 'st_nlink', 'st_rdev', 'st_size', 'st_uid']:
        try:
            stat_values[f] = stat.__getattribute__(f)
        except AttributeError:
            pass
    return stat_values


