#-*- coding: utf-8 -*-
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

#To test keys in redis
from redis import Redis
r = Redis()
k = r.keys('*:embargoed')
k2 = r.keys('*:embargoed_until')
ka = r.keys('*')
len(ka)
for i in ka:
    if not 'embargoed' in i:
        print i

r.llen('silochanges')
for i in range(r.llen('silochanges')):
    r.lindex('silochanges', i)
    
#======================================================================

# To add items to SOLR once in redis (for testing). Stop supervisor workers
from redis import Redis
from recordsilo import Granary
from solr import SolrConnection
from solr_worker import gather_document
import simplejson

r = Redis()
r.llen('silochanges')
for i in range(r.llen('silochanges')):
    r.lindex('silochanges', i)

g = Granary("/opt/RDFDatabank/silos")
solr = SolrConnection("http://localhost:8080/solr")

line = r.rpop("silochanges")
msg = simplejson.loads(line)
silo_name = msg['silo']
s = g.get_rdf_silo(silo_name)
itemid = msg.get('id')
if itemid and s.exists(itemid):
    item = s.get_item(itemid)
    solr_doc = gather_document(silo_name, item)
    solr.add(_commit=True, **solr_doc)

#r.rpush("silochanges", line)

#======================================================================

# To add items to redis
from rdfdatabank.lib.broadcast import BroadcastToRedis
b = BroadcastToRedis("localhost", 'silochanges')

b.creation("demo", "Apocalypse-auctm315", ident="admin")
b.creation("demo", "Apocalypse-douce249", ident="admin")
b.creation("demo", "BibliaPauperum-archgc14", ident="admin")
b.creation("demo", "CanticumCanticorum-auctm312", ident="admin")
b.creation("demo", "MCSimulation-WW4jet", ident="admin")
b.creation("demo", "MCSimulation-WW4jet-CR", ident="admin")
b.creation("demo", "MonteCarloSimulations", ident="admin")
b.creation("demo", "blockbooks", ident="admin")
b.creation("test", "TestSubmission_2", ident="sandbox_user")
b.creation("dataflow", "GabrielTest", ident="admin")
b.creation("dataflow", "anusha-test", ident="admin")
b.creation("dataflow", "anusha-test-testrdf3", ident="admin")
b.creation("dataflow", "anusha:test", ident="admin")
b.creation("dataflow", "joe-test-2011-09-16-1", ident="admin")
b.creation("dataflow", "joetest", ident="admin")
b.creation("dataflow", "monica-test", ident="admin")
b.creation("dataflow", "test123", ident="admin")
b.creation("dataflow", "testdir123", ident="admin")
b.creation("dataflow", "testdir2", ident="admin")
b.creation("dataflow", "unpackingTest", ident="admin")

#======================================================================
"""
To install the correct versions of Redis-server and python-redis, 
download the latest packages from oneiric

cd ~
aptitude show redis-server
sudo apt-get remove --purge redis-server
wget http://ubuntu.intergenia.de/ubuntu//pool/universe/r/redis/redis-server_2.2.11-3_amd64.deb
sudo dpkg -i redis-server_2.2.11-3_amd64.deb

cd ~
sudo rm -r /usr/local/lib/python2.6/dist-packages/redis-1.34.1-py2.6.egg
sudo apt-get remove --purge python-redis
wget http://de.archive.ubuntu.com/ubuntu/pool/universe/p/python-redis/python-redis_2.4.5-1_all.deb
sudo dpkg -i python-redis_2.4.5-1_all.deb
"""
