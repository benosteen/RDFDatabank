from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import rest
from datetime import datetime

from rdflib import Literal

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
from rdfdatabank.lib.HTTP_request import HTTPRequest
from rdfdatabank.lib import short_pid
from rdfdatabank.lib.doi_helper import get_doi_metadata

from rdfdatabank.config.doi_config import OxDataciteDoi

class DatasetsController(BaseController):
   
    @rest.restrict('GET', 'POST', 'PUT', 'DELETE')
    def datasetview(self, silo, id):
        doi_api = HTTPRequest(endpointhost=OxDataciteDoi.endpoint_host)
        doi_api.setRequestUserPass(endpointuser=OxDataciteDoi.account, endpointpass=OxDataciteDoi.password)
        
        http_method = request.environ['REQUEST_METHOD']

        c.silo_name = silo
        granary_list = ag.granary.silos
        if not silo in granary_list:
            abort(404)
        c_silo = ag.granary.get_rdf_silo(silo)
        if not c_silo.exists(id):
            abort(404)

        item = c_silo.get_item(id)
        c.version = item.currentversion         
        vnum = request.params.get('version', '') or ""
        if vnum:
            item.set_version_cursor(vnum)
            c.version = vnum

        if http_method == "GET":
            #Get the doi corresponding to this dataset (either matches the version given or the latest doi version)
            dois = item.list_rdf_objects(item.uri, u"http://purl.org/ontology/bibo/doi")
            if not dois or not dois[0]:
                abort(404, 'DOI not registered for version %s of dataset %s'%(c.version, c.silo_name))

            #doi = None
            #dois_by_version = {}
            #for d in dois:
            #    doi_parts = doi.split('/')
            #    doi_version = doi_parts[1].rsplit('.', 1)[1]
            #    if doi_version == c.version:
            #        doi = d
            #    if doi_version and not int(doi_version.strip()) in dois_by_version.keys():
            #          dois_by_version[doi_version] = d
            #if not doi:
            #    #Get the doi corresponding to the latest version available
            #    doi_versions = dois_by_version.keys().sort()
            #    doi = dois_by_version[doi_versions[-1]]

            resource = "%s?doi=%s"%(OxDataciteDoi.endpoint_path_metadata, dois[0]) 
            (resp, respdata) = doi_api.doHTTP_GET(\
                resource=OxDataciteDoi.endpoint_path_metadata, \
                expect_type=OxDataciteDoi.content_type)            
            if resp.status != 200:
                if resp.status == 403:
                    #TODO: Confirm 403 is not due to authorization
                    msg = "403 Forbidden - login error with Datacite or dataset belongs to another party at Datacite."
                elif resp.status == 404:
                    msg = "404 Not Found - DOI does not exist in DatCite's database"
                elif resp.status == 410:
                    msg = "410 Gone - the requested dataset was marked inactive (using DELETE method) at Datacite"
                elif resp.status == 500:
                    msg = "500 Internal Server Error - Error retreiving the metadata from Datacite."
                else:                                  
                    msg = "Error retreiving the metadata from Datacite. %s"%str(resp.status)
                abort(resp.status, msg)
           
            # conneg:
            accept_list = None
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
                    c.metadata = respdata
                    return render('/doiview.html')
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'application/json; charset="UTF-8"'
                    response.status_int = 200
                    response.status = "200 OK"
                    return simplejson.dumps(str(respdata.decode('utf-8')))
                elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                    response.status_int = 200
                    response.status = "200 OK"
                    response.content_type = 'application/rdf+xml; charset="UTF-8"'
                    return respdata
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing staisfies - default to text/html
            return render('/doiview.html')

        if http_method == "POST":
            #1. Generate DOI
            #TODO: DO I use short pids or go with the current format???
            #Current format: doi_prefix/bodleianSilo_nameDataset_name.Version_number
            DOI = "%s/bodleian%s%s.%s"%(OxDataciteDoi.prefix, silo, id, c.version)
            #2. Add the DOI to the rdf metadata
            item.add_namespace('bibo', "http://purl.org/ontology/bibo/")
            item.add_triple(item.uri, u"bibo:doi", Literal(DOI))
            item.del_triple(item.uri, u"dcterms:modified")
            item.add_triple(item.uri, u"dcterms:modified", datetime.now())
            #3. Construct XML metadata
            metadata = get_doi_metadata(item)
            #3. register the DOI with Datacite
            

            #4. Post the metadata to  
            
                
                
        #tiny_pid = short_pid.encode_url(201103216782) 