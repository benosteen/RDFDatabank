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
from rdflib import URIRef
import simplejson
from collections import defaultdict

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
                  port=c.get(redis_section, "port")
                  )
    DB_ROOT = c.get(worker_section, "dbroot")
    rdfdb_config = Config("%s/production.ini" % DB_ROOT)
    granary_root = rdfdb_config.get("app:main", "granary.store", 0, {'here':DB_ROOT})
  
    g = Granary(granary_root)

    solr = SolrConnection(c.get(worker_section, "solrurl"))

    idletime = 2

    while(True):
        sleep(idletime)
        line = rq.pop()
        if not line:
            continue
        msg = simplejson.loads(line)
        # solr switch
        silo_name = msg['silo']
        if silo_name not in g.silos:
            raise NoSuchSilo
        s = g.get_rdf_silo(silo_name)
        if msg['type'] == "c" or msg['type'] == "u" or msg['type'] == "embargo":
            # Creation, update or embargo change
            itemid = msg.get('id')
            logger.info("Got creation message on id:%s in silo:%s" % (itemid, silo_name))
            if itemid and s.exists(itemid):
                item = s.get_item(itemid)
                solr_doc = gather_document(silo_name, item)
                try:
                    solr.add(_commit=True, **solr_doc)
                except Exception, e :
                    logger.error("Error adding document to solr id:%s in silo:%s\n" % (itemid, silo_name))
                    #f = open('/var/log/databank/solr_error.log', 'a')
                    #f.write("Error adding record (creating) id:%s in silo:%s\n" % (itemid, silo_name))
                    try:
                       logger.error("%s\n\n" %str(e))
                    except:
                       pass
            rq.task_complete()
        elif msg['type'] == "d":
            # Deletion
            itemid = msg.get('id')
            if itemid and s.exists(itemid):
                solr.delete(itemid)
                solr.commit()
            rq.task_complete()
