from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import rest
from datetime import datetime

from rdflib import Literal, URIRef

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
from rdfdatabank.lib.HTTP_request import HTTPRequest
from rdfdatabank.lib import short_pid
from rdfdatabank.lib.doi_helper import get_doi_metadata, doi_count

from rdfdatabank.config.doi_config import OxDataciteDoi

class DoiController(BaseController):
   
    @rest.restrict('GET', 'POST', 'PUT', 'DELETE')
    def datasetview(self, silo, id):
        #f = open('/opt/rdfdatabank/src/logs/doi_debug.log', 'a')
        #f.write('in datasetview\n')
        #f.close()
        doi_conf = OxDataciteDoi()
        doi_api = HTTPRequest(endpointhost=doi_conf.endpoint_host, secure=True)
        doi_api.setRequestUserPass(endpointuser=doi_conf.account, endpointpass=doi_conf.password)
        
        http_method = request.environ['REQUEST_METHOD']
        # conneg:
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            try:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]

        c.silo_name = silo
        c.id = id
        granary_list = ag.granary.silos
        if not silo in granary_list:
            abort(404)
        c_silo = ag.granary.get_rdf_silo(silo)
        if not c_silo.exists(id):
            abort(404)

        c.dois = None
        c.version_doi = None
        c.message = None
        c.resp_status = None
        c.resp_reason = None
        c.metadata = None

        item = c_silo.get_item(id)
        c.version = item.currentversion         
        vnum = request.params.get('version', '') or ""
        if vnum:
            vnum = str(vnum)
            if not vnum in item.manifest['versions']:
                abort(404, "Version %s of dataset %s not found"%(vnum, c.silo_name))
            item.set_version_cursor(vnum)
            c.version = vnum

        c.dois = item.list_rdf_objects(None, u"http://purl.org/ontology/bibo/doi")
        version_uri = "%s/version%s"%(item.uri(.strip'/'), c.version)
        c.version_doi = item.list_rdf_objects(URIRef(version_uri), u"http://purl.org/ontology/bibo/doi")
        if not c.version_doi or not c.version_doi[0]:
            c.version_doi = None
        else:
            c.version_doi = c.version_doi[0]

        if http_method == "GET":
            #Get the doi corresponding to this dataset (either matches the version given or the latest doi version)
            if not c.version_doi:
                #f = open('/opt/rdfdatabank/src/logs/doi_debug.log', 'a')
                #f.write('Could not find DOI\n')
                #f.close()
                mimetype = accept_list.pop(0)
                while(mimetype):
                    if str(mimetype).lower() in ["text/html", "text/xhtml"]:  
                        c.metadata = None
                        return render('/doiview.html')
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                c.message = 'DOI not registered for version %s of dataset %s'%(c.version, c.silo_name)
                return render('/doiview.html')
                #abort(404, 'DOI not registered for version %s of dataset %s'%(c.version, c.silo_name))

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

            resource = "%s?doi=%s"%(doi_conf.endpoint_path_metadata, c.version_doi[0]) 
            
            #f = open('/opt/rdfdatabank/src/logs/doi_debug.log', 'a')
            #f.write('Contacting bL\n')
            #f.close()
            (resp, respdata) = doi_api.doHTTP_GET(resource=resource, expect_type='application/xml')
            c.resp_reason = resp.reason
            c.resp_status = resp.status
            #f = open('/opt/rdfdatabank/src/logs/doi_debug.log', 'a')
            #f.write('BL response : %s\n'%str(resp.status))
            #f.close()
            if resp.status < 200 or >= 300:
                response.status_int = 400
                response.status = "400 Bad Request"
                response_msg = ''
                c.metadata = ''
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
                c.message = msg
            else:
                response.status_int = 200
                response.status = "200 OK"
                c.metadata = respdata
                response_msg = respdata
                
                #abort(404, "%s, %s"%(resp.status, resp.reason))
                #TODO CONTENT NEGOTIATION
                #return render('/doiview.html')
                
            # conneg:
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    return render('/doiview.html')
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'text/plain; charset="UTF-8"'
                    return str(respdata.decode('utf-8'))
                elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                    response.status_int = 200
                    response.status = "200 OK"
                    response.content_type = 'text/xml; charset="UTF-8"'
                    return response_msg
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing staisfies - default to text/html
            return render('/doiview.html')

        if http_method == "POST":
            #1a. If doi doen not exist for this version, generate doi
            register_doi = False
            if not c.version_doi and c.version_doi[0]:
                if not cnt:
                    abort(400, "Error generating DOI")
                register_doi = True
                tiny_pid = short_pid.encode_url(cnt) 
                c.version_doi = "%s/bodleian%s.%s"%(doi_conf.prefix, tiny_pid, c.version)
                #2. Add the DOI to the rdf metadata
                item.add_namespace('bibo', "http://purl.org/ontology/bibo/")
                item.add_triple(URIRef(version_uri), u"bibo:doi", Literal(c.version_doi))
                item.del_triple(item.uri, u"dcterms:modified")
                item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                item.sync()
            #1b. Construct XML metadata
            xml_metadata = get_doi_metadata(item)
            """
            if not xml_metadata and not register_doi:
                #2a. If the doi already exists and there is no xml metadata to update, return bad request
                c.message = "Coud not update matadata"
                response.status_int = 400
                response.status = "Bad request"
                c.metadata = ''
            elif not xml_metadata and register_doi:
                #2b. If the doi is not registered, but there is no xml metadata to update, register just the doi with datacite
                resource = "%s"%doi_conf.endpoint_path_doi
                body = "%s\n%s"%(c.version_doi, item.uri)
                body_unicode = unicode(body, "utf-8")
                (resp, respdata) = doi_api.doHTTP_POST(body_unicode, resource=resource, data_type='text/plain;charset=UTF-8')
                c.resp_reason = resp.reason
                c.resp_status = resp.status
                if resp.status < 200 or >= 300:
                    response.status_int = 400
                    response.status = "400 Bad Request"
                    response_msg = "DOI not registered"
                    c.metadata = ''
                    if resp.status == 400:
                        msg = "400 Bad Request - Request body must be exactly two lines: DOI and URL"
                    elif resp.status == 403:
                        #TODO: Confirm 403 is not due to authorization
                        msg = "403 Forbidden - From Datacite: login problem, quota excceded, wrong domain, wrong prefix"
                    elif resp.status == 500:
                        msg = "500 Internal Server Error - Error registering the DOI."
                    else:
                        msg = "Error retreiving the metadata from Datacite. %s"%str(resp.status)
                    c.message = msg
                else:
                    response.status_int = 200
                    response.status = "200 OK"
                    response_msg = 'DOI Registered. %s"%respdata
                    c.metadata = ''
                    c.message = "201 Created - DOI registered. %s"%respdata
            else: 
                #register the DOI and metadata with Datacite
                body_unicode = unicode(xml_metadata, "utf-8")
                resource = "%s?doi=%s&url=%s"%(doi_conf.endpoint_path_metadata, DOI, item.uri)
                (resp, respdata) = doi_api.doHTTP_POST(body_unicode, resource=resource, data_type='application/xml;charset=UTF-8')
                c.resp_reason = resp.reason
                c.resp_status = resp.status
                if resp.status < 200 or >= 300:
                    response.status_int = 400
                    response.status = "400 Bad Request"
                    response_msg = "DOI and metadata not registered"
                    c.metadata = body_unicode
                    if resp.status == 400:
                        msg = "400 Bad Request - Invalid XML metadata"
                    elif resp.status == 403:
                        #TODO: Confirm 403 is not due to authorization
                        msg = "403 Forbidden - From Datacite: login problem, quota excceded, wrong domain, wrong prefix"
                    elif resp.status == 500:
                        msg = "500 Internal Server Error - Error registering the DOI."
                    else:
                        msg = "Error retreiving the metadata from Datacite. %s"%str(resp.status)
                    c.message = msg
                else:
                    response.status_int = 200
                    response.status = "200 OK"
                    response_msg = body_unicode
                    c.metadata = body_unicode
                    c.message = "201 Created - DOI registered. %s"%respdata
            # conneg:
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    return render('/doiview.html')
                elif str(mimetype).lower() in ["text/plain", "application/json"]:
                    response.content_type = 'text/plain; charset="UTF-8"'
                    return str(respdata.decode('utf-8'))
                elif str(mimetype).lower() in ["application/rdf+xml", "text/xml"]:
                    response.status_int = 200
                    response.status = "200 OK"
                    response.content_type = 'text/xml; charset="UTF-8"'
                    return response_msg
                try:
                    mimetype = accept_list.pop(0)
                except IndexError:
                    mimetype = None
            #Whoops - nothing staisfies - default to text/html
            return render('/doiview.html')
            """
            #JUST FOR TESTING - Have commented the lines above to prevent posting to Datacite and displaying the metadata for checking
            cnt = doi_count()
            c.DOI = DOI
            c.metadata = xml_metadata
            return render('/doiview.html')

