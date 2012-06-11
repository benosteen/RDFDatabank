#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2012 University of Oxford

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from redisqueue import RedisQueue
from LogConfigParser import Config
from solrFields import solr_fields_mapping

import sys
from time import sleep
from datetime import datetime, timedelta
from rdflib import URIRef
import simplejson
from collections import defaultdict
from uuid import uuid4

from recordsilo import Granary
from solr import SolrConnection

import logging

logger = logging.getLogger("redisqueue")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

class NoSuchSilo(Exception):
  pass

def gather_document(silo_name, item):
    graph = item.get_graph()
    document = defaultdict(list)
    document['uuid'].append(item.metadata['uuid'])
    document['id'].append(item.item_id)
    document['silo'].append(silo_name)
    for (_,p,o) in graph.triples((URIRef(item.uri), None, None)):
        if str(p) in solr_fields_mapping:
            field = solr_fields_mapping[str(p)]
            if field == "aggregatedResource":
                if '/datasets/' in o:
                    fn = unicode(o).split('/datasets/')
                    if len(fn) == 2 and fn[1]:
                        document['filename'].append(unicode(fn[1]).encode("utf-8"))
            if field == "embargoedUntilDate":
                ans = u"%sZ"%unicode(o).split('.')[0]
                document[field].append(unicode(ans).encode("utf-8"))
            else:
                document[field].append(unicode(o).encode("utf-8"))
        else:
            document['text'].append(unicode(o).encode("utf-8"))
    document = dict(document)
    return document

if __name__ == "__main__":
    c = Config()
    redis_section = "redis"
    worker_section = "worker_solr"
    worker_number = sys.argv[1]
    if len(sys.argv) == 3:
        if "redis_%s" % sys.argv[2] in c.sections():
            redis_section = "redis_%s" % sys.argv[2]

    rq = RedisQueue(c.get(worker_section, "listento"), "solr_%s" % worker_number,
                  db=c.get(redis_section, "db"), 
                  host=c.get(redis_section, "host"), 
                  port=c.get(redis_section, "port"),
                  errorqueue=c.get(worker_section, "errorq")
                 )
    DB_ROOT = c.get(worker_section, "dbroot")
    rdfdb_config = Config("%s/production.ini" % DB_ROOT)
    granary_root = rdfdb_config.get("app:main", "granary.store", 0, {'here':DB_ROOT})
  
    g = Granary(granary_root)

    solr = SolrConnection(c.get(worker_section, "solrurl"))

    idletime = 2
    commit_time = datetime.now() + timedelta(hours=1)
    toCommit = False
    while(True):
        sleep(idletime)

        if datetime.now() > commit_time and toCommit:
            solr.commit()
            commit_time = datetime.now() + timedelta(hours=1)
            toCommit = False

        line = rq.pop()

        if not line:
            if toCommit:
                solr.commit()
                toCommit = False
                commit_time = datetime.now() + timedelta(hours=1)
            continue

        logger.debug("Got message %s" %str(line))

        toCommit = True
        msg = simplejson.loads(line)
        # get silo name
        try:
            silo_name = msg['silo']
        except:
            logger.error("Msg badly formed %s\n"%str(msg))
            rq.task_complete()
            continue
        # Re-initialize granary
        if silo_name not in g.silos and not msg['type'] == "d":
            g = Granary(granary_root)
            g.state.revert()
            g._register_silos()
            if silo_name not in g.silos:
                logger.error("Silo %s does not exist\n"%silo_name)
                rq.task_complete()
                #raise NoSuchSilo
                continue
        if msg['type'] == "c" or msg['type'] == "u" or msg['type'] == "embargo":
            s = g.get_rdf_silo(silo_name)
            # Creation, update or embargo change
            itemid = msg.get('id', None)
            logger.info("Got creation message on id:%s in silo:%s" % (itemid, silo_name))
            if itemid and s.exists(itemid):
                item = s.get_item(itemid)
                solr_doc = gather_document(silo_name, item)
                try:
                    solr.add(_commit=False, **solr_doc)
                except Exception, e :
                    logger.error("Error adding document to solr id:%s in silo:%s\n" % (itemid, silo_name))
                    try:
                       logger.error("%s\n\n" %str(e))
                    except:
                       pass
                    rq.task_failed()
                    continue
            else:
                silo_metadata = g.describe_silo(silo_name)
                solr_doc = {'id':silo_name, 'silo':silo_name, 'type':'Silo', 'uuid':uuid4().hex}
                solr_doc['title'] = silo_metadata['title']
                solr_doc['description'] = silo_metadata['description']
                solr.add(_commit=False, **solr_doc)
            rq.task_complete()
        elif msg['type'] == "d":
            # Deletion
            itemid = msg.get('id', None)
            if itemid:
                logger.info("Got deletion message on id:%s in silo:%s" % (itemid, silo_name))
                query='silo:"%s" AND id:"%s"'%(silo_name, itemid)
                solr.delete_query(query)
            elif silo_name:
                logger.info("Got deletion message on silo:%s" %silo_name)
                query='silo:"%s"'%silo_name
                solr.delete_query(query)
                #solr.commit()
            rq.task_complete()
