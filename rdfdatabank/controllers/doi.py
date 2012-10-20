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

from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from pylons.controllers.util import abort
from pylons.decorators import rest
from datetime import datetime
from rdflib import Literal, URIRef

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse
from rdfdatabank.lib.HTTP_request import HTTPRequest
from rdfdatabank.lib import short_pid
from rdfdatabank.lib.auth_entry import list_silos
from rdfdatabank.lib.doi_helper import get_doi_metadata, doi_count

from rdfdatabank.config.doi_config import OxDataciteDoi

class DoiController(BaseController):
    """Class to generate and register DOIs along with the metadata of the data-package (POST), 
       update the metadata registered with the DOI (PUT), delete the DOI (DELETE) and 
       to get the information (GET) registered with Datacite - the organization responsible for minting DOIs

    if the metadata for the data package is also under embargo, then a DOI cannot be registered for such data-packages
    """
    @rest.restrict('GET', 'POST', 'PUT', 'DELETE')
    def datasetview(self, silo, id):
        c.silo_name = silo
        c.id = id

        http_method = request.environ['REQUEST_METHOD']

        granary_list = list_silos()
        if not silo in granary_list:
            abort(404)

        c_silo = ag.granary.get_rdf_silo(silo)
        if not c_silo.exists(id):
            abort(404)

        if ag.metadata_embargoed:
            abort(403, "DOIs cannot be issued to data packages whose metadata ia also under embargo")

        ident = request.environ.get('repoze.who.identity')  
        c.ident = ident

        item = c_silo.get_item(id)

        creator = None
        if item.manifest and item.manifest.state and 'metadata' in item.manifest.state and item.manifest.state['metadata'] and \
            'createdby' in item.manifest.state['metadata'] and item.manifest.state['metadata']['createdby']:
            creator = item.manifest.state['metadata']['createdby']

        c.version = item.currentversion
        c.version_doi = None
        c.editor = False

        #Get version number
        vnum = request.params.get('version', '') or ""
        if vnum:
            vnum = str(vnum)
            if not vnum in item.manifest['versions']:
                abort(404, "Version %s of data package %s not found"%(vnum, c.silo_name))
            c.version = vnum

        if not (http_method == "GET"):
            #identity management of item 
            if not request.environ.get('repoze.who.identity'):
                abort(401, "Not Authorised")
            silos = ag.authz(ident)      
            if silo not in silos:
                abort(403, "Forbidden")
            silos_admin = ag.authz(ident, permission='administrator')
            silos_manager = ag.authz(ident, permission='manager')
            #if not (ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]):
            if not (ident['repoze.who.userid'] == creator or silo in silos_admin or silo in silos_manager):
                abort(403, "Forbidden")
        elif http_method == "GET":
            silos_admin = ag.authz(ident, permission='administrator')
            silos_manager = ag.authz(ident, permission='manager')
            #if ident['repoze.who.userid'] == creator or ident.get('role') in ["admin", "manager"]:
            if ident['repoze.who.userid'] == creator or silo in silos_admin or silo in silos_manager:
                c.editor = True

        version_uri = "%s/version%s"%(item.uri.rstrip('/'), c.version)
        c.version_doi = item.list_rdf_objects(URIRef(version_uri), u"http://purl.org/ontology/bibo/doi")
        if not c.version_doi or not c.version_doi[0]:
            c.version_doi = None
        else:
            c.version_doi = c.version_doi[0]

        doi_conf = OxDataciteDoi()
        doi_api = HTTPRequest(endpointhost=doi_conf.endpoint_host, secure=True)
        doi_api.setRequestUserPass(endpointuser=doi_conf.account, endpointpass=doi_conf.password)

        # conneg:
        accept_list = None
        if 'HTTP_ACCEPT' in request.environ:
            try:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "html")]
        if not accept_list:
            accept_list= [MT("text", "html")]

        c.message = None
        c.resp_status = None
        c.resp_reason = None
        c.metadata = None

        if http_method == "GET":
            #Get a list of all dois registered for this data package
            c.dois = {}
            for v in item.manifest['versions']:
                doi_ans = None
                doi_ans = item.list_rdf_objects(URIRef("%s/version%s"%(item.uri.rstrip('/'), v)), u"http://purl.org/ontology/bibo/doi")
                if doi_ans and doi_ans[0]:
                    c.dois[v] = doi_ans[0]

            c.heading = "Doi metadata information from Datacite"
            if not c.version_doi:
                mimetype = accept_list.pop(0)
                while(mimetype):
                    if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                        #Doint this to avoid displaying the erro page!!!
                        response.status_int = 200
                        response.status = "200 OK"
                        c.metadata = None
                        return render('/doiview.html')
                    try:
                        mimetype = accept_list.pop(0)
                    except IndexError:
                        mimetype = None
                c.message = 'DOI not registered for version %s of data package %s'%(c.version, c.silo_name)
                return render('/doiview.html')

            resource = "%s?doi=%s"%(doi_conf.endpoint_path_metadata, c.version_doi)
            (resp, respdata) = doi_api.doHTTP_GET(resource=resource, expect_type='application/xml')
            c.resp_reason = resp.reason
            c.resp_status = resp.status
            if resp.status < 200 or resp.status >= 300:
                response.status_int = 400
                response.status = "400 Bad Request"
                response_msg = ''
                c.metadata = ''
                if resp.status == 403:
                    #TODO: Confirm 403 is not due to authorization
                    msg = "403 Forbidden - login error with Datacite or data package belongs to another party at Datacite."
                elif resp.status == 404:
                    msg = "404 Not Found - DOI does not exist in DatCite's database"
                elif resp.status == 410:
                    msg = "410 Gone - the requested data package was marked inactive (using DELETE method) at Datacite"
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
            # conneg:
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    #Setting headers to 200 to avoid displaying the error page!!!
                    response.status_int = 200
                    response.status = "200 OK"
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
            #Setting headers to 200 to avoid displaying the error page!!!
            response.status_int = 200
            response.status = "200 OK"
            return render('/doiview.html')

        if http_method == "POST":
            item.set_version_cursor(c.version)
            #1a. If doi doen not exist for this version, generate doi
            register_doi = False
            if not c.version_doi:
                cnt = doi_count()
                if not cnt:
                    abort(400, "Error generating DOI")
                register_doi = True
                tiny_pid = short_pid.encode_url(cnt) 
                c.version_doi = "%s/bodleian%s.%s"%(doi_conf.prefix, tiny_pid, c.version)
            #1b. Construct XML metadata
            xml_metadata = get_doi_metadata(c.version_doi, item)
            c.metadata = xml_metadata
            #FOR TEST PURPOSES ONLY
            #xml_metadata = False
            if not xml_metadata and not register_doi:
                #2a. If the doi already exists and there is no xml metadata to update, return bad request
                c.message = "Coud not update matadata"
                response.status_int = 400
                response.status = "Bad request"
                c.metadata = ''
            elif not xml_metadata and register_doi:
                #2b. If the doi is not registered, but there is no xml metadata to update, register just the doi with datacite
                c.heading = "Registering new DOI with Datacite"
                resource = "%s"%doi_conf.endpoint_path_doi
                body = "%s\n%s"%(c.version_doi, version_uri)
                #body_unicode = unicode(body, "utf-8")
                body_unicode = unicode(body)
                (resp, respdata) = doi_api.doHTTP_POST(body_unicode, resource=resource, data_type='text/plain;charset=UTF-8')
                c.resp_reason = resp.reason
                c.resp_status = resp.status
                if resp.status < 200 or resp.status >= 300:
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
                    #3. Add the DOI to the rdf metadata
                    item.add_namespace('bibo', "http://purl.org/ontology/bibo/")
                    item.add_triple(URIRef(version_uri), u"bibo:doi", Literal(c.version_doi))
                    item.del_triple(item.uri, u"dcterms:modified")
                    item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                    item.sync()
                    response.status_int = 200
                    response.status = "200 OK"
                    response_msg = "DOI Registered. %s"%respdata
                    c.metadata = ''
                    c.message = "201 Created - DOI registered. %s"%respdata
            else:
                #register the DOI and metadata with Datacite
                c.heading = "Registering new DOI along with its metadata with Datacite"
                #body_unicode = unicode(xml_metadata, "utf-8")
                #body_unicode = unicode(xml_metadata)
                body_unicode = xml_metadata
                resource = "%s?doi=%s&url=%s"%(doi_conf.endpoint_path_metadata, c.version_doi, version_uri)
                (resp, respdata) = doi_api.doHTTP_POST(body_unicode, resource=resource, data_type='application/xml;charset=UTF-8')
                c.resp_reason = resp.reason
                c.resp_status = resp.status
                if resp.status < 200 or resp.status >= 300:
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
                    #3. Add the DOI to the rdf metadata
                    item.add_namespace('bibo', "http://purl.org/ontology/bibo/")
                    item.add_triple(URIRef(version_uri), u"bibo:doi", Literal(c.version_doi))
                    item.del_triple(item.uri, u"dcterms:modified")
                    item.add_triple(item.uri, u"dcterms:modified", datetime.now())
                    item.sync()
                    response.status_int = 200
                    response.status = "200 OK"
                    response_msg = body_unicode
                    c.metadata = body_unicode
                    c.message = "201 Created - DOI registered. %s"%respdata
            # conneg:
            mimetype = accept_list.pop(0)
            while(mimetype):
                if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                    #Setting headers to 200 to avoid displaying the error page!!!
                    response.status_int = 200
                    response.status = "200 OK"
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
            #Setting headers to 200 to avoid displaying the error page!!!
            response.status_int = 200
            response.status = "200 OK"
            return render('/doiview.html')

