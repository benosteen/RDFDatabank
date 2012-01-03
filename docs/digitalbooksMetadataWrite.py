from solr import SolrConnection
import json
import codecs

solrhost = "http://localhost:8080/solr"
s = SolrConnection(solrhost)

fieldnames = ['silo', 'id', 'uuid', 'aggregatedResource', 'created', 'creator', 'currentVersion', 'date', 'dateAccepted', 'dateCopyrighted', 'dateSubmitted', 'description', 'embargoStatus', 'embargoedUntilDate',  'mediator', 'isPartOf', 'isVersionOf', 'license', 'modified', 'publisher', 'rights', 'subject', 'timestamp', 'title', 'type']

solr_params = {}
solr_params['q'] = "silo:digitalbooks"
solr_params['wt'] = 'json'
solr_params['fl'] = ','.join(fieldnames)
solr_params['rows'] = 500000
solr_params['start'] = 0

solr_response = s.raw_query(**solr_params)

numFound = 0
docs = None
fname = "digitalbooks.csv"
delimiter = '$'

if solr_response:
    ans = json.loads(solr_response)
    numFound = ans['response'].get('numFound',None)
    try:
        numFound = int(numFound)
    except:
        numFound = 0
    docs = ans['response'].get('docs',None)
    if numfound > 0 and docs:    
        out_f = codecs.open(fname, 'a', 'utf-8')
        for row in docs:
            row_val = []
            for name in fieldnames:
                if name in row and row[name] and isinstance(row[name], basestring):
                    row_val.append(row[name])
                elif name in row and row[name] and isinstance(row[name], list):
                    row_val.append(";".join(row[name]))
                else:
                    row_val.append("")
            if row_val:
                out_f.write("%s\n" %delimiter.join(row_val)
        out_f.close()
    else:
        print 'The search resulted in no documents'
else:
    print 'The search resulted in no matches'

