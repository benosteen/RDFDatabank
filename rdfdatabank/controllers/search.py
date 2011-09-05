import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from pylons import app_globals as ag

from rdfdatabank.lib.base import BaseController, render

from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

log = logging.getLogger(__name__)

class SearchController(BaseController):

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
