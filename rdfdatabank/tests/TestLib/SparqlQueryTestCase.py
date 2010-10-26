#!/usr/bin/python
# $Id:  $
"""
HTTP and SPARQL query test case support functions 

$Rev: $
"""

import os, os.path
import sys
import unittest
import logging
import httplib
import base64
import mimetypes
import urllib
import urlparse
try:
    # Running Python 2.5 with simplejson?
    import simplejson as simplejson
except ImportError:
    import json as simplejson

if __name__ == "__main__":
    # For testing: 
    # add main library directory to python path if running stand-alone
    sys.path.append("..")

from MiscLib import TestUtils

logger = logging.getLogger('SparqlQueryTestCase')

# Originally copied from http://code.activestate.com/recipes/146306/:
def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

# Originally copied from http://code.activestate.com/recipes/146306/:
def encode_multipart_formdata(fields, files):
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

def bindingType(b):
    """
    Function returns the type of a variable binding.  Commonly 'uri' or 'literal'.
    """
    type = b['type']
    if type == "typed-literal" and b['datatype'] == "http://www.w3.org/2001/XMLSchema#string":
        type = 'literal' 
    return type

def findVarBindings(data, var):
    """
    Returns a list of (type,value) pairs to which the supplied variable is bound in the results
    """
    return [ (bindingType(b[var]),b[var]['value']) 
             for b in data['results']['bindings'] if var in b ]

def findBindingSets(data):
    """
    Returns a list of lists of (var:(type,value)) dictionaries from the supplied results
    """
    return [ dict([ (var,{'type':bindingType(bindset[var]), 'value':bindset[var]['value']} ) for var in bindset ]) 
             for bindset in data['results']['bindings'] ]

class SparqlQueryTestCase(unittest.TestCase):
    """
    Test simple query patterns against data in SPARQL endpoint
    
    Although this module appears as a test suite, its main intended use is as a class
    that can be subclassed in place of unittest.TestCase, providing additional methods
    for testing HTTP access and SPATRQL queries.
    """
    def setUp(self):
        # Default SPARQL endpoint details
        self._endpointhost = "localhost"
        self._endpointpath = "/sparqlquerytest"     # Really just a placeholder
        self._endpointuser = None
        self._endpointpass = None
        return

    def tearDown(self):
        return

    def setRequestEndPoint(self, endpointhost=None, endpointpath=None):
        if endpointhost or endpointpath:
            if endpointhost:
                self._endpointhost = endpointhost
                # Reset credentials if setting host
                self._endpointuser = None
                self._endpointpass = None
            if endpointpath: self._endpointpath = endpointpath
            logger.debug("setRequestEndPoint: endpointhost %s: " % self._endpointhost)
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

    def doRequest(self, command, resource, reqdata=None, reqheaders={}, expect_status=200, expect_reason="OK"):
        logger.debug(command+" "+self.getRequestUri(resource))
        if self._endpointuser:
            auth = base64.encodestring("%s:%s" % (self._endpointuser, self._endpointpass)).strip()
            reqheaders["Authorization"] = "Basic %s" % auth
        #print "Connect to "+self._endpointhost
        hc   = httplib.HTTPConnection(self._endpointhost)
        path = self.getRequestPath(resource)
        response     = None
        responsedata = None
        repeat       = 10
        while path and repeat > 0:
            repeat -= 1
            #print "Request "+command+", path "+path
            hc.request(command, path, reqdata, reqheaders)
            response = hc.getresponse()
            if response.status != 301: break
            path = response.getheader('Location', None)
            #print "Redirect to: "+path
            if path[0:6] == "https:":
                # close old connection, create new HTTPS connection
                hc.close()
                hc = httplib.HTTPSConnection(self._endpointhost)    # Assume same host for https:
            else:
                response.read()  # Seems to be needed to free up connection for new request
        logger.debug("Status: %i %s" % (response.status, response.reason))
        if expect_status != "*": self.assertEqual(response.status, expect_status)
        if expect_reason != "*": self.assertEqual(response.reason, expect_reason)
        responsedata = response.read()
        hc.close()
        return (response, responsedata)

    def doHTTP_GET(self,
            endpointhost=None, endpointpath=None, resource=None,
            expect_status=200, expect_reason="OK",
            expect_type="*/*"):
        reqheaders   = {
            "Accept":       expect_type
            }
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, responsedata) = self.doRequest("GET", resource, 
            reqheaders=reqheaders,
            expect_status=expect_status, expect_reason=expect_reason)
        if (expect_type.lower() == "application/json"): responsedata = simplejson.loads(responsedata)
        return responsedata

    def doQueryGET(self, query, 
            endpointhost=None, endpointpath=None, 
            expect_status=200, expect_reason="OK",
            JSON=False):
        self.setRequestEndPoint(endpointhost, endpointpath)
        encodequery  = urllib.urlencode({"query": query})
        self.doHTTP_GET(endpointpath=self.getRequestPath("?"+encodequery), 
            expect_status=expect_status, expect_reason=expect_reason,
            expect_type=("application/json" if JSON else None))
        return responsedata

    def doHTTP_POST(self, data, data_type="application/octet-strem",
            endpointhost=None, endpointpath=None, resource=None,
            expect_status=200, expect_reason="OK",
            expect_type="*/*"):
        reqheaders   = {
            "Content-type": data_type,
            "Accept":       expect_type
            }
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, responsedata) = self.doRequest("POST", resource,
            reqdata=data, reqheaders=reqheaders,
            expect_status=expect_status, expect_reason=expect_reason)
        if (expect_type.lower() == "application/json"): responsedata = simplejson.loads(responsedata)
        return responsedata

    def doQueryPOST(self, query, 
            endpointhost=None, endpointpath=None, 
            expect_status=200, expect_reason="OK",
            JSON=False):
        reqheaders = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept":       "application/json"
            }
        encodequery = urllib.urlencode({"query": query})
        return self.doHTTP_POST(
            encodequery, data_type="application/x-www-form-urlencoded",
            endpointhost=None, endpointpath=None, 
            expect_status=200, expect_reason="OK",
            expect_type=("application/json" if JSON else None))

    def doHTTP_DELETE(self,
            endpointhost=None, endpointpath=None, resource=None,
            expect_status=200, expect_reason="OK"):
        self.setRequestEndPoint(endpointhost, endpointpath)
        (response, _) = self.doRequest("DELETE", resource,
            expect_status=expect_status, expect_reason=expect_reason)
        return response.status

    def assertVarBinding(self, data, var, type, value):
        """
        Asserts that the results for 'var' containing a binding
        """
        self.assertTrue( (type, value) in findVarBindings(data, var),
            """Expected to find %s bound as %s:"%s" in query results"""%(var, type, value))

    def assertBinding(self, data, var, type=None, value=None):
        self.assertTrue(var in data['head']['vars'], "Expected variable %s binding in query results"%(var))        
        bindings = findBindingSets(data)
        found = False
        for b in bindings:
            if var in b:
                match = True
                match &= (type  == None) or (b[var]['type']  == type)
                match &= (value == None) or (b[var]['value'] == value)
                if match:
                    found = True
                    break
        self.assertTrue(found, "Expected to find %s bound with type %s to value %s"%(var, type, value))

    def assertBindingCount(self, data, count):
        bindings = len(data['results']['bindings'])        
        self.assertEqual(bindings, count, "Expected %i result bindings, found %i"%(count, bindings))

    def assertBindingSet(self, data, expectbindingset):
        """
        Asserts that a given set of variable bindings occurs in at least one of the 
        result variable bindings from a query.
        """
        found = False
        for resultbinding in findBindingSets(data):
            # For each query result...
            match = True
            for [var, expect] in expectbindingset:
                # For each expected variable binding
                self.assertTrue(var in data['head']['vars'], 
                    "Expected variable %s binding in query results"%(var))                    
                # If variable is not bound in result, continue to next result 
                if not var in resultbinding:
                    match = False
                    continue
                # Match details for single variable in binding set
                for facet in expect:
                    match &= facet in resultbinding[var] and resultbinding[var][facet] == expect[facet]
            # Exit if all variables matched in single binding
            if match: return
        # No matching binding found
        self.assertTrue(False, "Expected to find binding set %s"%(expectbindingset))

    def assertBindingSetPos(self, data, pos, expectbindingset):
        """
        Asserts that a given set of variable bindings occurs in at least one of the 
        result variable bindings from a query.
        """
        resultbinding = findBindingSets(data)[pos]
        for [var, expect] in expectbindingset:
            # For each expected variable binding
            self.assertTrue(var in data['head']['vars'], "Expected variable %s binding in query results"%(var))                    
            # If variable is not bound in result, continue to next result 
            self.assertTrue(var in resultbinding, "Expected variable %s binding in query results"%(var))
            # Match details for single variable in binding set
            for facet in expect:
                self.assertTrue(
                    (facet in resultbinding[var] and resultbinding[var][facet] == expect[facet]), 
                    "Result %i expected binding set %s"%(pos,expectbindingset))

    # Actual tests follow

    def testNull(self):
        # Just checking that this module compiles and loads OK
        assert True, 'Null test failed'

    # Sentinel/placeholder tests

    def testUnits(self):
        assert (True)

    def testComponents(self):
        assert (True)

    def testIntegration(self):
        assert (True)

    def testPending(self):
        assert (False), "Pending tests follow"

# Assemble test suite

def getTestSuite(select="unit"):
    """
    Get test suite

    select  is one of the following:
            "unit"      return suite of unit tests only
            "component" return suite of unit and component tests
            "all"       return suite of unit, component and integration tests
            "pending"   return suite of pending tests
            name        a single named test to be run
    """
    testdict = {
        "unit":
            [ "testUnits"
            , "testNull"
            ],
        "component":
            [ "testComponents"
            ],
        "integration":
            [ "testIntegration"
            ],
        "pending":
            [ "testPending"
            ]
        }
    return TestUtils.getTestSuite(SparqlQueryTestCase, testdict, select=select)

if __name__ == "__main__":
    TestUtils.runTests("SparqlQueryTestCase.log", getTestSuite, sys.argv)

# End.
