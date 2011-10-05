#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import codecs
try:
    # Running Python 2.5 with simplejson?
    import simplejson as json
except ImportError:
    import json

#My system is running rdflib version 2.4.2. So adding rdflib v3.0 to sys path
#rdflib_path = os.path.join(os.getcwd(), 'rdflib')
#sys.path.insert(0, rdflib_path)
#import rdflib
#from rdflib.namespace import RDF
#from rdflib.graph import Graph
#from rdflib.plugins.memory import Memory
#from rdflib import URIRef
#from rdflib import Literal
#rdflib.plugin.register('sparql',rdflib.query.Processor,'rdfextras.sparql.processor','Processor')
#rdflib.plugin.register('sparql', rdflib.query.Result,
#                       'rdfextras.sparql.query', 'SPARQLQueryResult')

from StringIO import StringIO

from rdflib import RDF, URIRef, Literal
from rdflib.Graph import ConjunctiveGraph as Graph

#from time import sleep
#import subprocess

if __name__ == "__main__":
    # For testing: 
    # add main library directory to python path if running stand-alone
    sys.path.append("..")

#from MiscLib import TestUtils
from testlib import TestUtils
from testlib import SparqlQueryTestCase

#from RDFDatabankConfigProd import RDFDatabankConfig as RC
from RDFDatabankConfig import RDFDatabankConfig as RC

RDFDatabankConfig = RC()
logger = logging.getLogger('TestSubmission')

class TestSubmission(SparqlQueryTestCase.SparqlQueryTestCase):
    """
    Test simple dataset submissions to RDFDatabank
    """
    def setUp(self):
        self.setRequestEndPoint(
            endpointhost=RDFDatabankConfig.endpointhost,  # Via SSH tunnel
            endpointpath=RDFDatabankConfig.endpointpath)
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointuser,
            endpointpass=RDFDatabankConfig.endpointpass)
        self.setRequestUriRoot(
            manifesturiroot=RDFDatabankConfig.granary_uri_root)
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointuser,
            endpointpass=RDFDatabankConfig.endpointpass)
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")
        return

    def tearDown(self):
        return

    # Create empty test submission dataset
    def createSubmissionDataset(self, dataset_id='TestSubmission'):
        # Create a new dataset, check response
        fields = \
            [ ("id", dataset_id)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/%s"%(self._endpointpath, dataset_id)
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        return

    def uploadSubmissionZipfile(self, dataset_id='TestSubmission', file_to_upload="testdir.zip", filename=None):
        # Submit ZIP file, check response
        fields = []
        if filename:
            fields = \
                [ ("filename", filename)
                ]
        else:
            filename = file_to_upload
        zipdata = open("testdata/%s"%file_to_upload).read()
        files = \
            [ ("file", file_to_upload, zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/%s/"%dataset_id, 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/%s/%s"%(self._endpointpath, dataset_id, filename)
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        return zipdata

    def updateSubmissionZipfile(self, dataset_id='TestSubmission', file_to_upload="testdir.zip", filename=None):
        # Submit ZIP file, check response
        fields = []
        if filename:
            fields = \
                [ ("filename", filename)
                ]
        zipdata = open("testdata/%s"%file_to_upload).read()
        files = \
            [ ("file", file_to_upload, zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata)= self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/%s/"%dataset_id, 
            expect_status=204, expect_reason="No Content")
        return zipdata

    # Actual tests follow
    def test01CreateSilo(self):
        """List all silos your account has access to - GET /admin. If the silo 'sandbox' does not exist, create it"""
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointadminuser,
            endpointpass=RDFDatabankConfig.endpointadminpass)
        # Access list silos, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath="/",
            resource="admin/",
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        silo_name = RDFDatabankConfig.endpointpath.strip('/')
        silolist = data
        if not silo_name in silolist:
            #Create new silo
            owner_list = [RDFDatabankConfig.endpointadminuser]
            if not RDFDatabankConfig.endpointuser in owner_list:
                owner_list.append(RDFDatabankConfig.endpointuser)
            owner_list = ",".join(owner_list)
            fields = \
                [ ("silo", silo_name),
                  ("title", "Sandbox silo"),
                  ("description", "Sandbox silo for testing"),
                  ("notes", "Created by test"),
                  ("owners", owner_list),
                  ("disk_allocation", "100000")
                ]
            files =[]
            (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
            (resp,respdata) = self.doHTTP_POST(
                reqdata, reqtype, resource="admin/", endpointpath="/",
                expect_status=201, expect_reason="Created")
            LHobtained = resp.getheader('Content-Location', None)
            LHexpected = "/%s"%silo_name
            self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
            # Access list silos, check response
            (resp, data) = self.doHTTP_GET(
                endpointpath="/",
                resource="admin/",
                expect_status=200, expect_reason="OK", expect_type="application/json")
            newsilolist = data
            self.failUnless(len(newsilolist)>0, "No silos returned")
            self.assertEquals(len(newsilolist), len(silolist)+1, "One additional silo should have been returned")
            for s in silolist: self.failUnless(s in newsilolist, "Silo "+s+" in original list, not in new list")
            self.failUnless(silo_name in newsilolist, "Silo '%s' not in new list"%silo_name)
        return

    def testFileUploadBulk(self):
        for i in range(0, 10000):       
            """Upload file to dataset - POST file to /silo_name/datasets/dataset_name"""
            # Create a new dataset, check response
            start = datetime.now()
            dataset_id='TestSubmission%d'%i
            f = open('test_times.log', 'a')
            f.write('%s: Creating and uploading file to dataset %s \n'%(start.isoformat(), dataset_id))
            f.close()
            self.createSubmissionDataset(dataset_id=dataset_id)
            #Access state information
            (resp, respdata) = self.doHTTP_GET(
                resource="states/%s"%dataset_id, 
                expect_status=200, expect_reason="OK", expect_type="application/json")
            # Upload zip file, check response
            zipdata = self.uploadSubmissionZipfile(dataset_id=dataset_id, file_to_upload='rdfdatabank.zip', filename='testdir.zip')
            end = datetime.now()
            delta = end - start
            time_used = delta.days * 86400 + delta.seconds
            f = open('test_times.log', 'a')
            f.write('    Time taken: %s \n\n'%str(time_used))
            f.close()
            # Access and check list of contents
            (resp, rdfdata) = self.doHTTP_GET(
                resource="datasets/%s"%dataset_id, 
                expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
            rdfgraph = Graph()
            rdfstream = StringIO(rdfdata)
            rdfgraph.parse(rdfstream) 
            subj  = URIRef(self.getRequestUri("datasets/%s"%dataset_id))
            base = self.getRequestUri("datasets/%s/"%dataset_id)
            dcterms = "http://purl.org/dc/terms/"
            ore  = "http://www.openarchives.org/ore/terms/"
            oxds = "http://vocab.ox.ac.uk/dataset/schema#"
            stype = URIRef(oxds+"DataSet")
            self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
            self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
            self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
            self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
            self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
            self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
            self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
            self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
            self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
            self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
            self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
            # Access and check zip file content
            (resp, zipfile) = self.doHTTP_GET(
                resource="datasets/%s/testdir.zip"%dataset_id,
                expect_status=200, expect_reason="OK", expect_type="application/zip")
            self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
            #Access state information and check
            (resp, data) = self.doHTTP_GET(
                resource="states/%s"%dataset_id, 
                expect_status=200, expect_reason="OK", expect_type="application/json")
            state = data['state']
            parts = data['parts']
            self.assertEqual(len(state.keys()), 11, "States")
            self.assertEqual(state['item_id'], dataset_id, "Submission item identifier")
            self.assertEqual(len(state['versions']), 2, "Two versions")
            self.assertEqual(state['versions'][0], '0', "Version 0")
            self.assertEqual(state['versions'][1], '1', "Version 1")
            self.assertEqual(state['currentversion'], '1', "Current version == 1")
            self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
            self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
            self.assertEqual(state['files']['0'], ['manifest.rdf'], "List should contain just manifest.rdf")
            self.assertEqual(len(state['files']['1']), 2, "List should contain manifest.rdf and testdir.zip")
            self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
            self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
            self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
            self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
            self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
            self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
            self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed until?")
            self.assertEqual(len(parts.keys()), 4, "Parts")
            self.assertEqual(len(parts['4=%s'%dataset_id].keys()), 13, "File stats for 4=%s"%dataset_id)
            self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
            self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")
 
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
            , "test01CreateSilo"
            , "testFileUploadBulk"
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
    return TestUtils.getTestSuite(TestSubmission, testdict, select=select)

if __name__ == "__main__":
    TestUtils.runTests("TestSubmission.log", getTestSuite, sys.argv)

# End.
