#!/usr/bin/python
# $Id:  $
"""
Databank submission test cases

$Rev: $
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
from rdflib.Graph import ConjunctiveGraph as Graph

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
    def testCreateSilo(self):
        """List all silos your account has access to - GET /silo"""
        #Write a test to list all the silos. Test to see if it returns 200 OK and the list of silos is not empty
        # Access list silos, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/",
            resource="admin/", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        #Create new silo
        #print data
        #print type(data)
        #silolist = []
        #for k in data:
        #    silolist.append(k)
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
        #print "LHobtained:", LHobtained
        #print "LHexpected:", LHexpected
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
        
    def testSiloInfo(self):
        """Get admin informaton of a silo - GET /silo_name/admin"""
        #print "test silos is:", self.testsilo
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
        
    def testUpdateSiloInfo(self):
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
        
    def testDeleteSilo(self):
        #Is test silo - sandbox. If yes, create another silo
        #if self.testsilo == 'sandbox':
        #    self.testsilo = self.testsilo + '123'
        #    fields = \
        #        [ ("silo", 'sandbox123'),
        #            ("title", "Sandbox silo"),
        #            ("description", "Sandbox silo for testing"),
        #            ("notes", "Created by test"),
        #            ("owners", RDFDatabankConfig.endpointadminuser),
        #            ("disk_allocation", "100000")
        #        ]
        #    files =[]
        #    (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        #    (resp,respdata) = self.doHTTP_POST(
        #        reqdata, reqtype, endpointpath="/", resource="admin/",
        #        expect_status=201, expect_reason="Created")
        #    LHobtained = resp.getheader('Content-Location', None)
        #    LHexpected = "%s"%self.testsilo
        #    self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
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
            , "testCreateSilo"
            , "testSiloInfo"
            , "testUpdateSiloInfo"
            , "testDeleteSilo"
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
