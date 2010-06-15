from datetime import datetime, timedelta

from redis import Redis
import simplejson

from pylons import app_globals as ag

import re

ID_PATTERN = re.compile(r"^[0-9A-z\-\:]+$")

def authz(granary_list, ident):
    def _parse_owners(silo_name):
        g = ag.granary
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

