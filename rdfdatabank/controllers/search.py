# -*- coding: utf-8 -*-
import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort

from pylons import app_globals as ag

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.search_term import term_list
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

class SearchController(BaseController):

    def __before__(self):
        c.all_fields = term_list().get_all_search_fields()
        c.field_names = term_list().get_search_field_dictionary()
        c.facetable_fields = term_list().get_all_facet_fields()
        c.search_fields = ['silo', 'id', 'uuid', 'embargoStatus', 'embargoedUntilDate', 'currentVersion', 'doi', 'publicationDate', 'abstract', 'description', 'creator', 'isVersionOf', 'isPartOf', 'subject']
        c.sort_options = {'score desc':'Relevance',  'publicationDate desc':'Date (Latest to oldest)','publicationDate asc':'Date (Oldest to Latest)','silo asc':'Silo A to Z','silo desc':'Silo Z to A'}

    def raw(self):
        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident

        silos = None
        if ag.metadata_embargoed:
            if not ident:
                abort(401, "Not Authorised")
            granary_list = ag.granary.silos
            silos = ag.authz(granary_list, ident)

        if silos and not isinstance(silos, basestring) and type(silos).__name__ == 'list':
            silos = ' '.join(silos)
               
        http_method = request.environ['REQUEST_METHOD']        
        if http_method == "GET":
            params = request.GET
        elif http_method == "POST":
            params = request.POST

        if not "q" in params:
            abort(400, "Parameter 'q' is not available")

        #If ag.metadata_embargoed, search only within your silos
        if params['q'] == '*':
            if silos:
                params['q'] = """silo:(%s)"""%silos
            else:
                params['q'] = "*:*"
        elif silos and not 'silo:' in params['q']:
            params['q'] = """%s AND silo:(%s)"""%(params['q'], silos)        

        accept_list = None
        if 'wt' in params and params['wt'] == "json":
            accept_list = [MT("application", "json")]
        elif 'wt' in params and params['wt'] == "xml":
            accept_list = [MT("text", "xml")]
        else:                       
            if 'HTTP_ACCEPT' in request.environ:
                try:
                    accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
                except:
                    accept_list= [MT("text", "html")]
            if not accept_list:
                accept_list= [MT("text", "html")]

            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    params['wt'] = 'json'
                    accept_list= [MT("text", "html")]
                    break                 
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    params['wt'] = 'json'
                    accept_list= [MT("application", "json")]
                    break
                elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                    params['wt'] = 'xml'
                    accept_list = [MT("text", "xml")]
                    break
                # Whoops - nothing satisfies
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None

        if not 'wt' in params or not params['wt'] in ['json', 'xml']:
            params['wt'] = 'json'
            accept_list= [MT("text", "html")]        
        if not 'fl' in params or not params['fl']:
            #Also include the following fields - date modified, publication year / publication date, embargo status, embargo date, version
            params['fl'] = "id,silo,mediator,creator,title,score"
        if not 'start' in params or not params['start']:
            params['start'] = '0'
        if not 'rows' in params or not params['rows']:
            params['rows'] = '100'
                    
        result = ag.solr.raw_query(**params)
        
        mimetype = accept_list.pop(0)
        while(mimetype):
            if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                c.result = result                    
                return render('/raw_search.html')        
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                response.content_type = 'application/json; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return result
            elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                response.content_type = 'text/xml; charset="UTF-8"'
                response.status_int = 200
                response.status = "200 OK"
                return result
            # Whoops - nothing satisfies
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops - nothing staisfies - default to text/html
        c.result = result         
        return render('/raw_search.html')

    def detailed(self, query=None, additional_fields=[]):

        if query:
            c.q = query
        else:        
            c.q = request.params.get('q', None)
        if not c.q or c.q == '*':
            c.q = "*:*"
 
        # Search controls
        truncate = request.params.get('truncate', None)
        start = request.params.get('start', None)
        rows = request.params.get('rows', None)
        sort = request.params.get('sort', None)
        format = request.params.get('format', None)
        if not format:
            format = 'html'
        

        c.sort = 'score desc'
        # Lock down the sort parameter.
        if sort and sort in c.sort_options:
            c.sort = sort
        c.sort_text = c.sort_options[c.sort]
        
        c.chosen_fields = []
        c.chosen_fields.extend(c.search_fields)

        for fld in additional_fields:
            if not fld in c.chosen_fields:
                c.chosen_fields.append(fld)

        c.fields_to_facet = []
        c.fields_to_facet.extend(c.facetable_fields)

        c.facet_limit = 10

        c.chosen_facets = {}
        
        query_filter = ""
        
        #Setup to capture all the url parameters needed to regenerate this search
        c.search = {}
        filter_url = ""
        
        for field in c.all_fields:
            if request.params.get("filter"+field, None):
                multi = request.params.getall("filter"+field)
                c.chosen_facets[field] = []
                #c.search["filter"+field] = ""
                for m in multi:
                    try:
                        m = unquote(m)
                    except:
                        pass
                    m = m.strip()
                    m = m.strip('"')
                    c.chosen_facets[field].append(m)
                    query_filter += ' AND %s:"%s"'%(field, m)
                    try:
                        filter_url += '&filter%s=%s'%(field, quote('"%s"'%m))
                    except:
                        filter_url += '&filter%s=%s'%(field, '"%s"'%m)
                #if field in c.fields_to_facet:
                #    del c.fields_to_facet[field]
        
        for field in c.chosen_facets:
            if field not in c.chosen_fields:
                c.chosen_fields.append(field)

        c.truncate = 450
        c.start = 0
        c.rows = 5
        
        # Parse/Validate search controls
        if truncate:
            try:
                c.truncate = int(truncate)
                if c.truncate < 10:
                    c.truncate = 10
                if c.truncate > 1000:
                    c.truncate = 1000
            except ValueError:
                pass
                
        if start:
            try:
                c.start = int(start)
                if c.start < 0:
                    c.start = 0
            except ValueError:
                pass

        if rows:
            try:
                c.rows = int(rows)
                if c.rows < 5:
                    c.rows = 5
            except ValueError:
                pass
            
        #c.search['rows'] = c.rows
        c.search['truncate'] = c.truncate
        #c.search['start'] = c.start
        #c.search['sort'] = c.sort
        if c.q:
            c.search['q'] = c.q.encode('utf-8')
        solr_params = {}
        
        if c.q:
            solr_params['q'] = c.q.encode('utf-8')+query_filter+query_fulltext 

            if format in ['json', 'xml', 'python', 'php']:
                solr_params['wt'] = format
            else:
                solr_params['wt'] = 'json'

            solr_params['fl'] = ','.join(c.chosen_fields)
            solr_params['rows'] = c.rows
            solr_params['start'] = c.start

            if c.sort:
                solr_params['sort'] = c.sort
                 
            if c.fields_to_facet:
                solr_params['facet'] = 'true'
                solr_params['facet.limit'] = c.facet_limit
                solr_params['facet.mincount'] = 1
                solr_params['facet.field'] = []
                for facet in c.fields_to_facet:
                    solr_params['facet.field'].append(facet)
        
            solr_response = ag.solr.search(**solr_params)
        
            c.add_facet =  u"%ssearch/detailed?" % (g.root)
            c.add_facet = c.add_facet + urlencode(c.search) + filter_url
 
            if not solr_response:
                # FAIL - do something here:
                c.message = 'Sorry, either that search "%s" resulted in no matches, or the search service is not functional.' % c.q
                h.redirect_to(controller='/search', action='index')
        
            if format == 'atom':
                atom_gen = Solrjson(response=solr_response)
                atom_gen.create_atom(title="ORA Search: <em>%s</em>" % c.q, link="http://oradev.bodleian.ox.ac.uk", author="Oxford University Research Archive", url_prefix="http://oradev.bodleian.ox.ac.uk/objects/")
                response.headers['Content-Type'] = 'application/atom+xml'
                response.charset = 'utf8'
                c.atom = atom_gen.get_atom()
                return render('atom_results')
            elif format == 'xml':
                response.headers['Content-Type'] = 'application/xml'
                response.charset = 'utf8'
                c.atom = solr_response
                return render('atom_results')
            elif format == 'json':
                response.headers['Content-Type'] = 'application/json'
                response.charset = 'utf8'
                return solr_response
            elif format in ['csv', 'python', 'php']:
                response.headers['Content-Type'] = 'application/text'
                response.charset = 'utf8'
                return solr_response
                
            search = simplejson.loads(solr_response)
                
            numFound = search['response'].get('numFound',None)
            
            c.numFound = 0
            c.permissible_offsets = []
            
            c.pages_to_show = 5
            
            try:
                c.numFound = int(numFound)
                remainder = c.numFound % c.rows
                if remainder > 0:
                    c.lastPage = c.numFound - remainder
                else:
                    c.lastPage = c.numFound - c.rows
                
                if c.numFound > c.rows:
                    offset_start = c.start - ( (c.pages_to_show/2) * c.rows )
                    if offset_start < 0:
                        offset_start = 0
                    
                    offset_end = offset_start + (c.pages_to_show * c.rows)
                    if offset_end > c.numFound:
                        offset_end = c.numFound
                        if remainder > 0:
                            offset_start = c.lastPage - (c.pages_to_show * c.rows)
                        else:
                            offset_start = c.lastPage - ((c.pages_to_show-1) * c.rows)
                        
                        if offset_start < 0:
                            offset_start = 0
                    
                    c.permissible_offsets = list( xrange( offset_start, offset_end, c.rows) )
            except ValueError:
                pass

            c.docs = search['response'].get('docs',None)
        
            if c.fields_to_facet:
                c.returned_facets = {}
                for facet in search['facet_counts']['facet_fields']:       
                    facet_list = search['facet_counts']['facet_fields'][facet]
                    keys = facet_list[::2]
                    values = facet_list[1::2]
                    c.returned_facets[facet] = []
                    for index in range(len(keys)):
                        c.returned_facets[facet].append((keys[index],values[index]))

        return render('search_form')