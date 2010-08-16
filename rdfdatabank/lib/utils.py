from datetime import datetime, timedelta

from redis import Redis
import simplejson

from pylons import app_globals as ag

from rdfobject.constructs import Manifest

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
            item.metadata['embargoed_until'] = embargoed_until
        elif embargo_days_from_now:
            item.metadata['embargoed_until'] = (datetime.now() + timedelta(days=embargo_days_from_now)).isoformat()
        else:
            item.metadata['embargoed_until'] = (datetime.now() + timedelta(days=365*70)).isoformat()
    item.add_triple(item.uri, u"dcterms:dateSubmitted", datetime.now())
    if title:
        item.add_triple(item.uri, u"rdfs:label", title)
    item.sync()
    return item

def get_readme_text(item, filename="README"):
    with item.get_stream(filename) as fn:
        text = fn.read().decode("utf-8")
    return u"%s\n\n%s" % (filename, text)
    
def test_rdf(text):
    try:
        mani = Manifest()
        mani.from_string(text)
        return True
    except:
        return False

def munge_rdf(target_dataset_uri, manifest_file):
    triples = []
    namespaces = {}
    F = open(manifest_file, 'r')
    manifest_str = F.read()
    #if not test_rdf(manifest_str):
    #    return False
    mani = Manifest()
    mani.from_string(manifest_str)
    namespaces = mani.namespaces
    for s_uri in mani.items_rdfobjects:
        datasetType = False
        for t in mani.items_rdfobjects[s_uri].types:
            if str(t) == 'http://vocab.ox.ac.uk/dataset/schema#Grouping':
                datasetType = True
        if datasetType:
            #Add to existing uri and add a sameAs triple with this uri
            for s,p,o in mani.items_rdfobjects[s_uri].list_triples():
                triples.append((target_dataset_uri, p, o))
            namespaces['owl'] = "http://www.w3.org/2002/07/owl#"
            triples.append((target_dataset_uri, 'owl:sameAs', s_uri))
        else:
            for s,p,o in mani.items_rdfobjects[s_uri].list_triples():
                triples.append((s, p, o))
    return namespaces, triples
