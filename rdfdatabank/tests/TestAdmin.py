#!/usr/bin/python
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

"""
Databank submission test cases
"""

import os, os.path
from datetime import datetime, timedelta
import sys
import unittest
import logging
import httplib
import urllib
try:
    # Running Python 2.5 with simplejson?
    import simplejson as json
except ImportError:
    import json

from StringIO import StringIO

from rdflib import RDF, URIRef, Literal
#from rdflib.Graph import ConjunctiveGraph as Graph
from rdflib import ConjunctiveGraph as Graph

if __name__ == "__main__":
    # For testing: 
    # add main library directory to python path if running stand-alone
    sys.path.append("..")

#from MiscLib import TestUtils
from testlib import TestUtils
from testlib import SparqlQueryTestCase

from RDFDatabankConfig import RDFDatabankConfig

logger = logging.getLogger('testAdmin')

class TestAdmin(SparqlQueryTestCase.SparqlQueryTestCase):
    """
    Test simple dataset submissions to RDFDatabank
    """
    def setUp(self):
        #super(TestAdmin, self).__init__()
        self.setRequestEndPoint(
            endpointhost=RDFDatabankConfig.endpointhost,
            endpointpath=RDFDatabankConfig.endpointpath)
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointadminuser,
            endpointpass=RDFDatabankConfig.endpointadminpass)
        self.setRequestUriRoot(
            manifesturiroot=RDFDatabankConfig.granary_uri_root)
        self.testsilo = 'tessst'
        return

    def tearDown(self):
        return

    # Actual tests follow
    def test1CreateSilo(self):
        """List all silos your account has access to - GET /silo"""
        #Write a test to list all the silos. Test to see if it returns 200 OK and the list of silos is not empty
        # Access list silos, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/",
            resource="admin/", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        #Create new silo
        silolist = data
        fields = \
            [ ("silo", self.testsilo),
              ("title", "Sandbox silo"),
              ("description", "Sandbox silo for testing"),
              ("notes", "Created by test"),
              ("owners", RDFDatabankConfig.endpointadminuser),
              ("disk_allocation", "100000")
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, resource="admin/", endpointpath="/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "/%s"%self.testsilo
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access list silos, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/",
            resource="admin/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        #newsilolist = []
        #for k in data:
        #    newsilolist.append(k)
        newsilolist = data
        self.failUnless(len(newsilolist)>0, "No silos returned")
        self.assertEquals(len(newsilolist), len(silolist)+1, "One additional silo should have been returned")
        for s in silolist: self.failUnless(s in newsilolist, "Silo "+s+" in original list, not in new list")
        self.failUnless(self.testsilo in newsilolist, "Silo "+self.testsilo+" not in new list")
        return   
        
    def test2SiloInfo(self):
        """Get admin informaton of a silo - GET /silo_name/admin"""
        # Access silo information in admin, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/%s/"%self.testsilo,
            resource="admin/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # check silo name and base_uri
        self.assertEqual(data['title'], "Sandbox silo", "Silo title is %s not 'Sandbox silo'" %data['title'])
        self.assertEqual(data['description'], "Sandbox silo for testing", "Silo title is '%s' not 'Sandbox silo for testing'" %data['description'])
        self.assertEqual(data['notes'], "Created by test", "Silo notes is '%s' not 'Created by test'" %data['notes'])
        self.assertEqual(data['owners'], RDFDatabankConfig.endpointadminuser, "Silo owner is '%s' not '%s'" %(data['owners'], RDFDatabankConfig.endpointadminuser))
        self.assertEqual(data['disk_allocation'], "100000", "Silo title is '%s' not '100000'" %data['disk_allocation'])
        return
        
    def test3UpdateSiloInfo(self):
        """Update silo metadata"""
        fields = \
            [ ("silo", self.testsilo),
              ("title", "Sandbox silo"),
              ("description", "Sandbox silo for testing"),
              ("notes", "Created by test"),
              ("owners", "%s,%s"%(RDFDatabankConfig.endpointadminuser,RDFDatabankConfig.endpointuser)),
              ("disk_allocation", "200000")
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(reqdata, reqtype,
            endpointpath="/%s/"%self.testsilo, resource="admin/",
            expect_status=204, expect_reason="Updated", expect_type="text/plain")
        # Access silo information in admin, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/%s/"%self.testsilo, 
            resource="admin/",
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # check silo name and base_uri
        self.assertEqual(data['title'], "Sandbox silo", "Silo title is %s not 'Sandbox silo'" %data['title'])
        self.assertEqual(data['description'], "Sandbox silo for testing", "Silo title is '%s' not 'Sandbox silo for testing'" %data['description'])
        self.assertEqual(data['notes'], "Created by test", "Silo notes is '%s' not 'Created by test'" %data['notes'])
        self.assertEqual(data['owners'], "%s,%s"%(RDFDatabankConfig.endpointadminuser,RDFDatabankConfig.endpointuser), "Silo owner is '%s' not '%s,%s'" %(data['owners'], RDFDatabankConfig.endpointadminuser,RDFDatabankConfig.endpointuser))
        self.assertEqual(data['disk_allocation'], "200000", "Silo title is '%s' not '200000'" %data['disk_allocation'])
        return
        
    def test4DeleteSilo(self):
        """Delete silo test"""
        #Delete Silo
        resp = self.doHTTP_DELETE(
            endpointpath="/%s/"%self.testsilo, 
            resource="admin/", 
            expect_status=200, expect_reason="OK")
        # Access silo, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/%s/"%self.testsilo, 
            resource="admin/",
            expect_status=403, expect_reason="Forbidden")
        return
    
    # Sentinel/placeholder tests

    def testUnits(self):
        assert (True)

    def testComponents(self):
        assert (True)

    def testIntegration(self):
        assert (True)

    def testPending(self):
        #Need to have performance tests and analyse performance
        #Need to set the permission of file being uploaded
        #assert (False), "Pending tests follow"
        assert (True)
   
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
            , "test1CreateSilo"
            , "test2SiloInfo"
            , "test3UpdateSiloInfo"
            , "test4DeleteSilo"
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
    return TestUtils.getTestSuite(TestAdmin, testdict, select=select)

if __name__ == "__main__":
    TestUtils.runTests("TestAdmin.log", getTestSuite, sys.argv)

# End.
