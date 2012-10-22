from solr import SolrConnection

from frontend.settings import SOLR_HOST

import json

solr_conn = SolrConnection(SOLR_HOST)

def formatDate(dt):
    dt_human = dt
    try:
        dt_obj = parse(dt, dayfirst=True, yearfirst=False)
        dt_human = dt_obj.strftime("%B %d %Y, %I:%M %p")
    except:
        return dt
    return dt_human

def getSiloModifiedDate(silo_name):
    solr_params = {}
    solr_params['q'] = "silo:%s"%silo_name
    solr_params['wt'] = 'json'
    solr_params['start'] = 0
    solr_params['rows'] = 1
    solr_params['sort'] = "modified desc"
    solr_params['fl'] = 'modified'
    solr_response = None
    try:
        solr_response = solr.raw_query(**solr_params)
    except:
        pass
    if not solr_response:
        return ''
    result = json.loads(solr_response)
    docs = result['response'].get('docs',None)
    numFound = result['response'].get('numFound',None)
    if docs and len(docs) > 0 and docs[0] and 'modified' in  docs[0] and len(docs[0]['modified']) > 0:
        dt = docs[0]['modified'][0]
    else:
        return ''
    dt = formatDate(dt)
    return dt 

