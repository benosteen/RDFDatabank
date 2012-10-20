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

import logging
import mimetypes
import httplib
import base64
import urlparse
import json as simplejson

logger = logging.getLogger('Dataset')

class HTTPRequest():
    def __init__(self, endpointhost=None, secure=False):
        if endpointhost:
            self._endpointhost = endpointhost
            self._endpointpath = None
        self.secure = secure

    def get_content_type(self, filename):
        # Originally copied from http://code.activestate.com/recipes/146306/:
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def get_data_type(self, params):
        files = []
        fields = []
        decoded_params = params.items()
        for i in decoded_params:
            if len(i) == 2:
                fields.append(i)
            elif len(i) == 4:
                files.append(i)
        return fields, files

    def encode_multipart_formdata(self, fields, files):
        # Originally copied from http://code.activestate.com/recipes/146306/:
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value, filetype) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value, filetype) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % (filetype or get_content_type(filename)))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def setRequestEndPoint(self, endpointhost=None, endpointpath=None):
        if endpointhost or endpointpath:
            if endpointhost:
                self._endpointhost = endpointhost
                # Reset credentials if setting host
                self._endpointuser = None
                self._endpointpass = None
                logger.debug("setRequestEndPoint: endpointhost %s: " % self._endpointhost)
            if endpointpath: 
                self._endpointpath = endpointpath           
                logger.debug("setRequestEndPoint: endpointpath %s: " % self._endpointpath)
        return
    
    def setRequestUserPass(self, endpointuser=None, endpointpass=None):
        if endpointuser:
            self._endpointuser = endpointuser
            self._endpointpass = endpointpass
            logger.debug("setRequestEndPoint: endpointuser %s: " % self._endpointuser)
            logger.debug("setRequestEndPoint: endpointpass %s: " % self._endpointpass)
        else:
            self._endpointuser = None
            self._endpointpass = None
        return

    def getRequestPath(self, rel):
        rel = rel or ""
        return urlparse.urljoin(self._endpointpath,rel)

    def getRequestUri(self, rel):
        return "http://"+self._endpointhost+self.getRequestPath(rel)

    def encodeFormData(self, params):
        (fields, files) = self.get_data_type(params)
        (reqtype, reqdata) = self.encode_multipart_formdata(fields, files)
        return reqtype, reqdata

    def doRequest(self, command, resource, reqdata=None, reqheaders={}):
        if self._endpointuser:
            auth = base64.encodestring("%s:%s" % (self._endpointuser, self._endpointpass)).strip()
            reqheaders["Authorization"] = "Basic %s" % auth
        if self.secure:
            hc = httplib.HTTPSConnection(self._endpointhost)
        else:
            hc   = httplib.HTTPConnection(self._endpointhost)
        path = self.getRequestPath(resource)
        response     = None
        responsedata = None
        repeat       = 10
        while path and repeat > 0:
            repeat -= 1
            hc.request(command, path, reqdata, reqheaders)
            response = hc.getresponse()
            if response.status != 301: break
            path = response.getheader('Location', None)
            if path[0:6] == "https:":
                # close old connection, create new HTTPS connection
                hc.close()
                hc = httplib.HTTPSConnection(self._endpointhost)    # Assume same host for https:
            else:
                response.read()  # Seems to be needed to free up connection for new request
        logger.debug("Status: %i %s" % (response.status, response.reason))
        responsedata = response.read()
        hc.close()
        return (response, responsedata)

    def doHTTP_GET(self, endpointhost=None, endpointpath=None, resource=None, expect_type="*/*"):
        reqheaders   = {
            "Accept":       expect_type
            }
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, responsedata) = self.doRequest("GET", resource, reqheaders=reqheaders)
        #ctype = response.getheader('content-type')
        #if (responsedata and expect_type.lower() == "application/json"): responsedata = simplejson.loads(responsedata)
        #if (responsedata and "application/json" in ctype): responsedata = simplejson.loads(responsedata)
        return (response, responsedata)

    def doHTTP_POST(self, data, data_type="application/octet-strem",
            endpointhost=None, endpointpath=None, resource=None, expect_type="*/*"):
        reqheaders   = {
            "Content-type": data_type,
            "Accept":       expect_type
            }
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, responsedata) = self.doRequest("POST", resource, reqdata=data, reqheaders=reqheaders)
        #ctype = response.getheader('content-type')
        #if (responsedata and expect_type.lower() == "application/json"): responsedata = simplejson.loads(responsedata)
        #if (responsedata and "application/json" in ctype): responsedata = simplejson.loads(responsedata)
        return (response, responsedata)

    def doHTTP_PUT(self, data, data_type="application/octet-strem",
            endpointhost=None, endpointpath=None, resource=None, expect_type="*/*"):
        reqheaders   = {
            "Content-type": data_type,
            "Accept":       expect_type
            }
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, responsedata) = self.doRequest("PUT", resource, reqdata=data, reqheaders=reqheaders)
        #ctype = response.getheader('content-type')
        #if (responsedata and "application/json" in ctype): responsedata = simplejson.loads(responsedata)
        return (response, responsedata)

    def doHTTP_DELETE(self, endpointhost=None, endpointpath=None, resource=None):
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, responsedata) = self.doRequest("DELETE", resource)
        return (response, responsedata)

