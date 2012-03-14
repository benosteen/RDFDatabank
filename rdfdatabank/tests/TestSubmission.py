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
from dateutil.relativedelta import *
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
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")
        return

    def tearDown(self):
        return

    # Create empty test submission dataset
    def createSubmissionDataset(self, embargoed=None, embargoed_until=None):
        # Create a new dataset, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        if embargoed != None:
            if embargoed:
                fields.append(('embargoed', 'True'))
            else:
                fields.append(('embargoed', 'False'))
        if embargoed_until != None:
            if embargoed_until == True:
                fields.append(('embargoed_until', 'True'))
            elif embargoed_until == False:
                fields.append(('embargoed_until', 'False'))
            else:
                fields.append(('embargoed_until', embargoed_until))
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        return

    def uploadSubmissionZipfile(self, file_to_upload="testdir.zip"):
        # Submit ZIP file, check response
        fields = []
        zipdata = open("testdata/%s"%file_to_upload).read()
        files = \
            [ ("file", file_to_upload, zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/%s"%(self._endpointpath, file_to_upload)
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        return zipdata

    def updateSubmissionZipfile(self, file_to_upload="testdir.zip", filename=None):
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
            resource="datasets/TestSubmission/", 
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

    def testListSilos(self):
        """List all silos your account has access to - GET /silo"""
        #Write a test to list all the silos. Test to see if it returns 200 OK and the list of silos is not empty
        # Access list silos, check response
        (resp, data) = self.doHTTP_GET(
            endpointpath=None,
            resource="/silos/", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # check list of silos is not empty
        self.failUnless(len(data)>0, "No silos returned")
   
    def testListDatasets(self):
        """List all datasets in a silo - GET /silo_name/datasets"""
        # Access list of datasets in the silo, check response
        (resp, data) = self.doHTTP_GET(
            resource="datasets/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Save initial list of datasets
        datasetlist = []
        for k in data:
            datasetlist.append(k)
        # Create a new dataset
        self.createSubmissionDataset()
        # Read list of datasets, check that new list is original + new dataset
        (resp, data) = self.doHTTP_GET(
            resource="datasets/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        newlist = []
        for k in data:
            newlist.append(k)
        logger.debug("Orig. length "+str(len(datasetlist))+", new length "+str(len(newlist)))
        self.assertEquals(len(newlist), len(datasetlist)+1, "One additional dataset")
        for ds in datasetlist: self.failUnless(ds in newlist, "Dataset "+ds+" in original list, not in new list")
        for ds in newlist: self.failUnless((ds in datasetlist) or (ds == "TestSubmission"), "Datset "+ds+" in new list, not in original list")
        self.failUnless("TestSubmission" in newlist, "testSubmission in new list")
        # Delete new dataset
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # read list of datasets, check result is same as original list
        (resp, data) = self.doHTTP_GET(
            resource="datasets/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        newlist = []
        for k in data:
            newlist.append(k)
        logger.debug("Orig. length "+str(len(datasetlist))+", new length "+str(len(newlist)))
        self.assertEquals(len(newlist), len(datasetlist), "Back to original content in silo")
        for ds in datasetlist: self.failUnless(ds in newlist, "Datset "+ds+" in original list, not in new list")
        for ds in newlist: self.failUnless(ds in datasetlist, "Datset "+ds+" in new list, not in original list")

    def testSiloState(self):
        """Get state informaton of a silo - GET /silo_name/states"""
        # Access state information of silo, check response
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointadminuser,
            endpointpass=RDFDatabankConfig.endpointadminpass)
        (resp, data) = self.doHTTP_GET(
            resource="states/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # check silo name and base_uri
        silo_name = RDFDatabankConfig.endpointpath.strip('/')
        silo_base  = URIRef(self.getManifestUri("datasets/"))
        self.assertEqual(data['silo'], silo_name, 'Silo name is %s not %s' %(data['silo'], silo_name))
        self.assertEqual(data['uri_base'].strip(), silo_base.strip(), 'Silo uri_base is %s not %s' %(data['uri_base'], silo_base))
        #self.failUnless(len(data['datasets'])>0, "No datasets returned")
        self.failUnless('datasets' in data, "datasets info for silo not returned")
        self.failUnless((type(data['datasets']).__name__ == 'dict'), "Datasets with embargo info not returned for silo")
        # Save initial list of datasets
        datasetlist = data['datasets']
        # Create a new dataset
        self.createSubmissionDataset()
        # Read list of datasets, check that new list is original + new dataset
        (resp, data) = self.doHTTP_GET(
            resource="states/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        newlist = data['datasets']
        logger.debug("Orig. length "+str(len(datasetlist))+", new length "+str(len(newlist)))
        self.assertEquals(len(newlist), len(datasetlist)+1, "One additional dataset")
        for ds in datasetlist: self.failUnless(ds in newlist, "Dataset "+ds+" in original list, not in new list")
        for ds in newlist: self.failUnless((ds in datasetlist) or (ds == "TestSubmission"), "Datset "+ds+" in new list, not in original list")
        self.failUnless("TestSubmission" in newlist, "testSubmission in new list")
        # Delete new dataset
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # read list of datasets, check result is same as original list
        (resp, data) = self.doHTTP_GET(
            resource="states/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        newlist = data['datasets']
        logger.debug("Orig. length "+str(len(datasetlist))+", new length "+str(len(newlist)))
        self.assertEquals(len(newlist), len(datasetlist), "Back to original content in silo")
        for ds in datasetlist: self.failUnless(ds in newlist, "Datset "+ds+" in original list, not in new list")
        for ds in newlist: self.failUnless(ds in datasetlist, "Datset "+ds+" in new list, not in original list")

    def testDatasetNotPresent(self):
        """Verify dataset is not present - GET /silo_name/dataset_name"""
        (resp, respdata) = self.doHTTP_GET(resource="TestSubmission", expect_status=404, expect_reason="Not Found")

    def testDatasetCreation(self):
        """Create dataset - POST id to /silo_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')

    def testDatasetCreation2(self):
        """Create dataset - POST to /silo_name/dataset_name"""
        # Create a new dataset, check response
        fields = []
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata)= self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')

    def testDatasetRecreation(self):
        """Create dataset - POST existing id to /silo_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        #Recreate the dataset, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets",
            expect_status=409, expect_reason="Conflict: Dataset Already Exists")
        #Recreate the dataset, check response
        fields = []
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=400, expect_reason="Bad request")
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))

    def testDeleteDataset(self):
        """Delete dataset - DELETE /silo_name/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Access dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")

    def testDatasetNaming(self):
        """Create dataset - POST to /silo_name/dataset_name. If name is valid, return 201, else return 403"""
        names = [("TestSubmission-1", 201, "Created")
            ,("TestSubmission_2", 201, "Created")
            ,("TestSubmission:3", 201, "Created")
            ,("TestSubmission*4", 400, "Bad request. Dataset name not valid")
            ,("TestSubmission/5", 404, "Not Found")
            ,("TestSubmission\6", 400, "Bad request. Dataset name not valid")
            ,("TestSubmission,7", 400, "Bad request. Dataset name not valid")
            ,("TestSubmission&8", 400, "Bad request. Dataset name not valid")
            ,("TestSubmission.9", 400, "Bad request. Dataset name not valid")
            ,("""Test"Submission""", 400, "Bad request. Dataset name not valid")
            ,("Test'Submission", 400, "Bad request. Dataset name not valid")
            #,("""Test Submission""", 400, "Bad request. Dataset name not valid") #The name is truncated to Test and dataset is created. This does not happen when using the form
            ,("TestSubmission$", 400, "Bad request. Dataset name not valid")
            ,("T", 400, "Bad request. Dataset name not valid")
        ]
        fields = []
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        for name, status, reason in names:
            #Create a new dataset, check response
            (resp,respdata) = self.doHTTP_POST(
                reqdata, reqtype, 
                resource="datasets/%s"%name, 
                expect_status=status, expect_reason=reason)
            # Access dataset, check response
            if status == 201:
                LHobtained = urllib.unquote(resp.getheader('Content-Location', None))
                LHexpected = "%sdatasets/%s"%(self._endpointpath, name)
                self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
                (resp, rdfdata) = self.doHTTP_GET(
                    resource="datasets/%s"%name, 
                    expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
                rdfgraph = Graph()
                rdfstream = StringIO(rdfdata)
                rdfgraph.parse(rdfstream) 
                self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
            elif status == 403:
                (resp, respdata) = self.doHTTP_GET(
                    resource="datasets/%s"%name, 
                    expect_status=404, expect_reason="Not Found")
        #Delete Datasets
        for name, status, reason in names:
            if not status == 201:
                continue
            resp = self.doHTTP_DELETE(
                resource="datasets/%s"%name, 
                expect_status=200, expect_reason="OK")

    def testDatasetStateInformation(self):
        """Get state information of dataset - GET /silo_name/states/dataset_name."""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 1, "Initially one version")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['currentversion'], '0', "Current version == 0")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(state['files']['0'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        # date
        # version_dates
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testEmbargoOnCreation(self):
        """Create dataset - POST id to /silo_name"""
        #---------------------------------------------------------------
        # Create a new dataset, check response. No embargo information is passed.
        self.createSubmissionDataset()
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.assertTrue((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        d = (datetime.now() + relativedelta(years=+70)).isoformat()
        d = d.split('T')[0]
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue(d in state['metadata']['embargoed_until'], "embargoed_until %s?"%d)
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed=None, embargo_until=True.
        self.createSubmissionDataset(embargoed_until=True)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.assertTrue((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        d = (datetime.now() + relativedelta(years=+70)).isoformat()
        d = d.split('T')[0]
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue(d in state['metadata']['embargoed_until'], "embargoed_until %s?"%d)
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed=None, embargo_until=2012-08-12
        d = '2012-08-12'
        self.createSubmissionDataset(embargoed_until=d)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.assertTrue((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        d = (datetime.now() + relativedelta(years=+70)).isoformat()
        d = d.split('T')[0]
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue(d in state['metadata']['embargoed_until'], "embargoed_until %s?"%d)
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed=True, embargo_until=None.
        self.createSubmissionDataset(embargoed=True)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed?")
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed=True, embargo_until=True
        self.createSubmissionDataset(embargoed=True, embargoed_until=True)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        d = (datetime.now() + relativedelta(years=+70)).isoformat()
        d = d.split('T')[0]
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue(d in state['metadata']['embargoed_until'], "embargoed_until %s?"%d)
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed=True, embargo_until=09-08-2012
        d = '09-08-2012'
        self.createSubmissionDataset(embargoed=True, embargoed_until=d)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2012-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2012-08-09?")
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed = False. 
        self.createSubmissionDataset(embargoed=False)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed?")
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed = False, embargoed_until = True
        self.createSubmissionDataset(embargoed=False, embargoed_until=True)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed?")
        #---------------------------------------------------------------
        # Delete dataset, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")
        #---------------------------------------------------------------
        # Create a new dataset, check response. embargoed = False, embargoed_until = 12 sep 2013
        d = '12 Sep 2013'
        self.createSubmissionDataset(embargoed=False, embargoed_until=d)
        # Access dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        # Access state info
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed?")


    def testFileUpload(self):
        """Upload file to dataset - POST file to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        #Access state information
        (resp, respdata) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile()
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
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
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testFileDelete(self):
        """Delete file in dataset - DELETE /silo_name/datasets/dataset_name/file_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile()
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        # Access and check zip file content and version
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        # Delete file, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission/testdir.zip", 
            expect_status=200, expect_reason="OK")
        # Access and check zip file does not exist
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=404, expect_reason="Not Found")
       # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['2']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testFileUpdate(self):
        """Update file in dataset - POST file to /silo_name/datasets/dataset_name (x 2)"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file, check response (uploads the file testdir.zip)
        zipdata = self.uploadSubmissionZipfile()
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission")) 
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        # Access and check zip file content and version
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        # Upload zip file again, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="testdir2.zip", filename="testdir.zip")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')  
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['2']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testGetDatasetByVersion(self):
        """Upload files to a dataset - POST file to /silo_name/datasets/dataset_name. Access each of the versions and the files in that version"""
        #Definitions
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        #---------Version 0
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        #---------Version 1
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile()
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        # Access and check list of contents of version 0
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version0", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        #---------Version 2
        # Upload zip file, check response
        zipdata2 = self.uploadSubmissionZipfile(file_to_upload="testdir2.zip")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile - testdir.zip!")
        (resp, zipfile2) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata2, zipfile2, "Difference between local and remote zipfile - testdir2.zip!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        #---------Version 3
        # Delete file, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission/testdir.zip", 
            expect_status=200, expect_reason="OK")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=404, expect_reason="Not Found")
        (resp, zipfile2) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata2, zipfile2, "Difference between local and remote zipfile - testdir2.zip!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        #---------Version 4
        # Update zip file, check response
        zipdata3 = self.updateSubmissionZipfile(file_to_upload="testrdf4.zip", filename="testdir2.zip")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=404, expect_reason="Not Found")
        (resp, zipfile2) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata3, zipfile2, "Difference between local and remote zipfile - testdir2.zip!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        #=========Access each of the versions
        #---------Version 0
        # Access and check list of contents of version 0
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version0", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission/version0", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        #---------Version 1
        # Access and check list of contents of version 1
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version1", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip/version1",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile - Version 1!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission/version1", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")
        #---------Version 2
        # Access and check list of contents of version 2
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version2", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip/version2",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile - Version 2!")
        (resp, zipfile2) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip/version2",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata2, zipfile2, "Difference between local and remote zipfile - Version 2!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission/version2", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")
        self.assertEqual(len(parts['testdir2.zip'].keys()), 13, "File stats for testdir2.zip")
        #---------Version 3
        # Access and check list of contents of version 3
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version3", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip/version3",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata2, zipfile, "Difference between local and remote zipfile - Version 3!")
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip/version3",
            expect_status=404, expect_reason="Not Found")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission/version3", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir2.zip'].keys()), 13, "File stats for testdir2.zip")
        #---------Version 4
        # Access and check list of contents of version 4
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version4", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'4') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip/version4",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata3, zipfile, "Difference between local and remote zipfile - Version 4!")
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip/version4",
            expect_status=404, expect_reason="Not Found")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission/version4", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 5, "Five versions")
        self.assertEqual(state['versions'],['0', '1', '2', '3', '4'], "Versions")
        self.assertEqual(state['currentversion'], '4', "Current version == 4")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(state['files']['0'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['2']), 3, "List should contain manifest.rdf, testdir.zip and testdir2.zip")
        self.assertEqual(len(state['files']['3']), 2, "List should contain manifest.rdf and testdir2.zip")
        self.assertEqual(len(state['files']['4']), 2, "List should contain manifest.rdf and testdir2.zip")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['metadata_files']['4']), 0, "metadata_files of version 4")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(len(state['subdir']['4']), 0,   "Subdirectory count for version 4")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir2.zip'].keys()), 13, "File stats for testdir2.zip")
        # Access and check list of contents of version 5
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission/version5", 
            expect_status=404, expect_reason="Not Found")
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2.zip/version5",
            expect_status=404, expect_reason="Not Found")
            
    def testPostMetadataFile(self):
        """POST manifest to dataset - POST manifest.rdf to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload metadata file, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="ww1-860b-manifest.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        owl = "http://www.w3.org/2002/07/owl#"
        bibo = "http://purl.org/ontology/bibo/"
        geo = "http://www.w3.org/2003/01/geo/wgs84_pos#"
        foaf = "http://xmlns.com/foaf/0.1/"
        address = "http://schemas.talis.com/2005/address/schema#"
        stype = URIRef(oxds+"DataSet")
        stype2 = URIRef(bibo+"DocumentPart")
        self.assertEqual(len(rdfgraph),42,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:piblisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,RDF.type,stype2) in rdfgraph, 'Testing submission type: '+subj+", "+stype2)
        self.failUnless((subj,URIRef(dcterms+"isPartOf"),URIRef("https://databank.ora.ox.ac.uk/ww1archives/datasets/ww1")) in rdfgraph, 'dcterms:isPartOf')
        self.failUnless((subj,URIRef(dcterms+"isPartOf"),URIRef("https://databank.ora.ox.ac.uk/ww1archives/datasets/ww1-1123")) in rdfgraph, 'dcterms:isPartOf')
        self.failUnless((subj,URIRef(dcterms+"creator"),"Thomas, Edward") in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(dcterms+"title"),"Two Houses") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(dcterms+"description"),"This manuscript is untitled but entitled 'Two Houses' in Edward Thomas Collected Poems") in rdfgraph, 'dcterms:description')
        self.failUnless((subj,URIRef(dcterms+"spatial"),"London") in rdfgraph, 'dcterms:spatial')
        self.failUnless((subj,URIRef(dcterms+"format"),"Notebook") in rdfgraph, 'dcterms:format')
        self.failUnless((subj,URIRef(dcterms+"medium"),"Paper") in rdfgraph, 'dcterms:medium')
        self.failUnless((subj,URIRef(dcterms+"type"),"Poem") in rdfgraph, 'dcterms:type')
        self.failUnless((subj,URIRef(bibo+"number"),"13") in rdfgraph, 'bibo:number')
        self.failUnless((subj,URIRef(dcterms+"source"),"MS Don d.28 f.13") in rdfgraph, 'dcterms:source')
        self.failUnless((subj,URIRef(dcterms+"contributor"),"Everett Sharp") in rdfgraph, 'dcterms:contributor')
        self.failUnless((subj,URIRef(dcterms+"identifier"),"ETBODDOND28-13.jpg") in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"rightsHolder"),"Copyright of The Bodleian Library, Oxford University / The Edward Thomas Literary Estate") in rdfgraph, 'dcterms:rightsHolder')
        self.failUnless((subj,RDF.value,"51.501") in rdfgraph, 'rdf:value')
        #self.failUnless((subj,URIRef(dcterms+"created"),"1915-07-22") in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"type"),URIRef("http://purl.org/dc/dcmitype/StillImage")) in rdfgraph, 'dcterms:type')
        self.failUnless((subj,URIRef(dcterms+"spatial"),None) in rdfgraph, 'dcterms:spatial')
        self.failUnless((None,URIRef(geo+"lat"),"51.501") in rdfgraph, 'geo:lat')
        self.failUnless((None,URIRef(geo+"long"),"-0.1254") in rdfgraph, 'geo:long')
        self.failUnless((subj,URIRef(bibo+"owner"),None) in rdfgraph, 'bibo:owner')
        self.failUnless((None,RDF.type,URIRef(foaf+"Organization")) in rdfgraph, 'rdf:type')
        self.failUnless((None,URIRef(foaf+"name"),"Bodleian Library, University of Oxford") in rdfgraph, 'foaf:name')
        self.failUnless((None,URIRef(address+"streetAddress"),"Western Manuscripts Collections") in rdfgraph, 'address:streetAddress')
        self.failUnless((None,URIRef(address+"streetAddress"),"Broad Street") in rdfgraph, 'address:streetAddress')
        self.failUnless((None,URIRef(address+"localityName"),"Oxford") in rdfgraph, 'address:localityName')
        self.failUnless((None,URIRef(address+"regionName"),"Oxfordshire") in rdfgraph, 'address:regionName')
        self.failUnless((None,URIRef(address+"postalCode"),"OX13BG") in rdfgraph, 'address:postalCode')
        self.failUnless((None,URIRef(address+"countryName"),"United Kingdom") in rdfgraph, 'address:countryName')
        self.failUnless((None,URIRef(foaf+"homepage"),"http://www.bodley.ox.ac.uk/") in rdfgraph, 'foaf:homepage')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['currentversion'], '1', "Current version == 1")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testMetadataFileUpdate(self):
        """POST manifest to dataset - POST manifest.rdf to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload metadata file, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        owl = "http://www.w3.org/2002/07/owl#"
        bibo = "http://purl.org/ontology/bibo/"
        geo = "http://www.w3.org/2003/01/geo/wgs84_pos#"
        foaf = "http://xmlns.com/foaf/0.1/"
        address = "http://schemas.talis.com/2005/address/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:piblisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        # Update metadata file, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="ww1-2862-manifest.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        stype2 = URIRef(bibo+"Document")
        doctext = """<br>  She had a name among the children;
<br>  But no one loved though someone owned
<br>  Her, locked her out of doors at bedtime
<br>  And had her kittens duly drowned.
<br>  In Spring, nevertheless, this cat
<br>  Ate blackbirds, thrushes, nightingales,
<br>  And birds of bright voice and plume and flight,
<br>  As well as scraps from neighbours' pails.
<br>  I loathed and hated her for this;
<br>  One speckle on a thrush's breast
<br>  Was worth a million such; and yet
<br>  She lived long, till God gave her rest.
<br><br>"""
        self.assertEqual(len(rdfgraph),32,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),'A Cat') in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://databank.ora.ox.ac.uk/ww1archives/datasets/ww1-2862")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,RDF.type,stype2) in rdfgraph, 'Testing submission type: '+subj+", "+stype2)
        self.failUnless((subj,URIRef(dcterms+"isPartOf"),URIRef("https://databank.ora.ox.ac.uk/ww1archives/datasets/ww1")) in rdfgraph, 'dcterms:isPartOf')
        self.failUnless((subj,URIRef(dcterms+"creator"),"Thomas, Edward") in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(dcterms+"type"),"Poem") in rdfgraph, 'dcterms:type')
        self.failUnless((subj,URIRef(dcterms+"type"),URIRef("http://purl.org/dc/dcmitype/Text")) in rdfgraph, 'dcterms:type')
        self.failUnless((subj,URIRef(dcterms+"rightsHolder"),"Copyright Edward Thomas, 1979, reproduced under licence from Faber and Faber Ltd.") in rdfgraph, 'dcterms:rightsHolder')
        self.failUnless((subj,RDF.value,Literal(doctext)) in rdfgraph, 'rdf:value')
        self.failUnless((subj,URIRef(dcterms+"source"),"Edward Thomas Collected Poems") in rdfgraph, 'dcterms:source')
        #self.failUnless((subj,URIRef(dcterms+"created"),"1979-01-01/1979-12-31") in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(bibo+"editor"),"Thomas, George") in rdfgraph, 'bibo:editor')
        self.failUnless((subj,URIRef(bibo+"owner"),None) in rdfgraph, 'bibo:owner')
        self.failUnless((None,RDF.type,URIRef(foaf+"Organization")) in rdfgraph, 'rdf:type')
        self.failUnless((None,URIRef(foaf+"name"),"ProQuest") in rdfgraph, 'foaf:name')
        self.failUnless((None,URIRef(foaf+"homepage"),"http://lion.chadwyck.co.uk/") in rdfgraph, 'foaf:homepage')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((None,URIRef(foaf+"name"),"Faber and Faber") in rdfgraph, 'foaf:name')
        self.failUnless((None,URIRef(address+"localityName"),"London") in rdfgraph, 'address:localityName')
        
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testMetadataFileDelete(self):
        """Delete manifest in dataset - DELETE /silo_name/datasets/dataset_name/manifest.rdf"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Delete metadata file, check response
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=403, expect_reason="Forbidden")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        dcterms = "http://purl.org/dc/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'0') in rdfgraph, 'oxds:currentVersion')

    def testPutCreateFile(self):
        """PUT file contents to new filename - PUT file contents to /silo_name/datasets/dataset_name/file_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Put zip file, check response
        zipdata = open("testdata/testdir.zip").read()       
        (resp, respdata) = self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/testdir.zip", 
            expect_status=201, expect_reason="Created", expect_type="text/plain")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/testdir.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
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
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testPutUpdateFile(self):
        """PUT file contents to existing filename - PUT file contents to /silo_name/datasets/dataset_name/file_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile(file_to_upload="testdir.zip")
        # Access content
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        # Put zip file, check response
        zipdata2 = open("testdata/testrdf3.zip").read()       
        (resp, respdata) = self.doHTTP_PUT(zipdata2, resource="datasets/TestSubmission/testrdf3.zip", 
            expect_status=201, expect_reason="Created", expect_type="text/plain")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/testrdf3.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission")) 
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        # Access and check zip file content and version
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        (resp, zipfile2) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testrdf3.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata2, zipfile2, "Difference between local and remote zipfile!")
        # Put zip file again, check response
        zipdata3 = open("testdata/testdir2.zip").read()       
        (resp, respdata) = self.doHTTP_PUT(zipdata3, resource="datasets/TestSubmission/testdir.zip", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')  
        # Access and check zip file content
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata3, zipfile, "Difference between local and remote zipfile!")
        (resp, zipfile2) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testrdf3.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata2, zipfile2, "Difference between local and remote zipfile!")
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 4, "Four versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['versions'][3], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(state['files']['0'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['2']), 3, "List should contain manifest.rdf, testdir.zip and testrdf3.zip")
        self.assertEqual(len(state['files']['3']), 3, "List should contain manifest.rdf, testdir.zip and testrdf3.zip")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")
        self.assertEqual(len(parts['testrdf3.zip'].keys()), 13, "File stats for testrdf3.zip")
        # Access and check zip file content of version 1
        (resp, zipfile) = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip/version1",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")

    def testPutMetadataFile(self):
        """Add metadata to manifest - PUT metadata to /silo_name/datasets/dataset_name/manifest.rdf"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Put manifest file, check response
        zipdata = open("testdata/manifest.rdf").read()       
        (resp, respdata) = self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        # Update metadata file, check response
        zipdata = open("testdata/manifest2.rdf").read()       
        (resp, respdata) = self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(dcterms+"title"),'Test dataset with updated and merged metadata') in rdfgraph, 'dcterms:title')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['subdir']['0']), 0,   "Subdirectory count for version 0")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        
    def testUnicodeMetadataFileUpdate(self):
        """POST/PUT manifest to dataset - /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()

        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"DataSet")
        # POST unicode file 01, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="unicodedata/unicode01.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext1 = None 
        f = codecs.open('testdata/unicodedata/unicode01.txt', 'r', 'utf-8')
        doctext1 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:piblisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),"General punctuation") in rdfgraph, 'dcterms:title')
        #for s, p, o in rdfgraph.triples((None, RDF.value, None)):
        #    print s, p, type(o), '\n',  o
        #print '\n', '-'*50
        #print  Literal(doctext1)
        #print '\n', '-'*50
        self.failUnless((subj,RDF.value,Literal(doctext1)) in rdfgraph, 'rdf:value')
        self.failUnless((subj,URIRef(dcterms+"source"),"http://www.madore.org/~david/misc/unitest/") in rdfgraph, 'dcterms:source')

        # PUT unicode file 02, check response
        manidata = open("testdata/unicodedata/unicode02.xml").read()       
        (resp, respdata) = self.doHTTP_PUT(manidata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        #Access state information and check
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext2 = None
        f = codecs.open('testdata/unicodedata/unicode02.txt', 'r', 'utf-8')
        doctext2 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),15,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"A table of (some) accents") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext2)) in rdfgraph, 'rdf:value')
        
        # PUT unicode file 03, check response
        manidata = open("testdata/unicodedata/unicode03.xml").read()       
        (resp, respdata) = self.doHTTP_PUT(manidata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        #Access state information and check
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext3 = None
        f = codecs.open('testdata/unicodedata/unicode03.txt', 'r', 'utf-8')
        doctext3 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),16,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Combining diacritics") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext3)) in rdfgraph, 'rdf:value')
        
        # POST unicode file 04, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="unicodedata/unicode04.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext4 = None 
        f = codecs.open('testdata/unicodedata/unicode04.txt', 'r', 'utf-8')
        doctext4 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'4') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Various symbols") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext4)) in rdfgraph, 'rdf:value')

        # POST unicode file 05, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="unicodedata/unicode05.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext5 = None 
        f = codecs.open('testdata/unicodedata/unicode05.txt', 'r', 'utf-8')
        doctext5 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),18,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'5') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Some verses in Russian") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext5)) in rdfgraph, 'rdf:value')
        
        # PUT unicode file 06, check response
        manidata = open("testdata/unicodedata/unicode06.xml").read()       
        (resp, respdata) = self.doHTTP_PUT(manidata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        #Access state information and check
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext6 = None
        f = codecs.open('testdata/unicodedata/unicode06.txt', 'r', 'utf-8')
        doctext6 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),19,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'6') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Some verses in ancient Greek") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext6)) in rdfgraph, 'rdf:value')
        
        # POST unicode file 07, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="unicodedata/unicode07.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext7 = None 
        f = codecs.open('testdata/unicodedata/unicode07.txt', 'r', 'utf-8')
        doctext7 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),20,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'7') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Some verses in Sanskrit") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext7)) in rdfgraph, 'rdf:value')

        # PUT unicode file 08, check response
        manidata = open("testdata/unicodedata/unicode08.xml").read()       
        (resp, respdata) = self.doHTTP_PUT(manidata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        #Access state information and check
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext8 = None
        f = codecs.open('testdata/unicodedata/unicode08.txt', 'r', 'utf-8')
        doctext8= f.read()
        f.close()
        self.assertEqual(len(rdfgraph),21,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'8') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Some Chinese") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext8)) in rdfgraph, 'rdf:value')
        
        # POST unicode file 09, check response
        zipdata = self.updateSubmissionZipfile(file_to_upload="unicodedata/unicode09.xml", filename="manifest.rdf")
        # Access and check list of contents
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext9 = None 
        f = codecs.open('testdata/unicodedata/unicode09.txt', 'r', 'utf-8')
        doctext9 = f.read()
        f.close()
        self.assertEqual(len(rdfgraph),22,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'9') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"A Tamil name") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext9)) in rdfgraph, 'rdf:value')
        
        # PUT unicode file 10, check response
        manidata = open("testdata/unicodedata/unicode10.xml").read()       
        (resp, respdata) = self.doHTTP_PUT(manidata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="text/plain")
        #Access state information and check
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        doctext10 = None
        f = codecs.open('testdata/unicodedata/unicode10.txt', 'r', 'utf-8')
        doctext10= f.read()
        f.close()
        self.assertEqual(len(rdfgraph),23,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'10') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"title"),"Some Arabic") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,RDF.value,Literal(doctext10)) in rdfgraph, 'rdf:value')
        os.remove('response.xml')

    def testDeleteEmbargo(self):
        """Delete embargo information - POST embargo_change to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        # Delete embargo, check response
        fields = \
            [ ("embargoed", 'false')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], "", "Should have no date for embargoed_until")
        
    def testChangeEmbargo(self):
        """Modify embargo information - POST embargo_change, embargo, embargo_until to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.assertTrue((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        d = (datetime.now() + relativedelta(years=+70)).isoformat()
        d = d.split('T')[0]
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue(d in state['metadata']['embargoed_until'], "embargoed_until %s?"%d)
        #-------------------------------------------------
        # Change embargo without embargo_until date - embargoed = True, check response
        fields = \
            [ ("embargoed", 'true')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "embargoed_until?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = True
        d = datetime.now().isoformat()
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", 'true')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        d = (datetime.now() + relativedelta(years=+70)).isoformat()
        d = d.split('T')[0]
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue(d in state['metadata']['embargoed_until'], "embargoed_until %s?"%d)
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = datetime
        d = datetime.now()
        delta = timedelta(days=365*4)
        d2 = d + delta
        d2 = d2.isoformat()
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),d2) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], d2, "embargoed_until?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = datetime
        d2 = '09 August 2013'
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'4') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2013-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2013-08-09?")
        #-------------------------------------------------
        # Change embargo - embargoed_until = true and check response
        fields = \
            [ ("embargoed_until", 'true')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=400, expect_reason="Bad request")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'4') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2013-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2013-08-09?")
        #-------------------------------------------------
        # Change embargo - embargoed_until = date and check response
        d5 = datetime.now()
        delta = timedelta(days=3)
        d5 = d5 + delta
        d5 = d5.isoformat()
        fields = \
            [ ("embargoed_until", d5)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=400, expect_reason="Bad request")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'4') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2013-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2013-08-09?")
        #-------------------------------------------------
        #Delete embargo
        fields = \
            [ ("embargoed", 'false')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'5') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed until?")
        #-------------------------------------------------
        #Delete embargo
        fields = \
            [ ("embargoed", 'false')
             ,("embargoed_until", 'true')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'6') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed until?")
        #-------------------------------------------------
        #Delete embargo
        d = datetime.now()
        delta = timedelta(days=4)
        d3 = d + delta
        d3 = d3.isoformat()
        fields = \
            [ ("embargoed", 'false')
             ,("embargoed_until", d3)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.assertFalse((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'7') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], '', "Embargoed until?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = '09 Aug 2013'
        d2 = '09 Aug 2013'
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'8') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2013-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2013-08-09?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = '09 08 2015'
        d2 = '09 08 2015'
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'9') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2015-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2015-08-09?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = '09-08-16'
        d2 = '09-08-16'
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'10') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2016-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2016-08-09?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = '09/08/17'
        d2 = '09/08/17'
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'11') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2017-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2017-08-09?")
        #-------------------------------------------------
        #Change embargo - embargoed = true, embargoed_until = 'Aug 09, 2018'
        d2 = 'Aug 09, 2018'
        fields = \
            [ ("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'12') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertTrue('2018-08-09' in state['metadata']['embargoed_until'], "embargoed_until 2018-08-09?")
        #-------------------------------------------------

    def testFileUnpack(self):
        """Unpack zip file to a new dataset - POST zip filename to /silo_name/items/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testdir"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access parent dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access new dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getManifestUri("datasets/TestSubmission-testdir/")
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:locense')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        # Access and check content of a resource
        (resp, filedata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="text/plain")
        checkdata = open("testdata/testdir/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        #Access state information of TestSubmission-testdir
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['currentversion'], '1', "Current version == 1")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 3, "List should contain manifest.rdf, testdir and test-csv.csv")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(state['subdir']['0'], [],   "Subdirectory for version 0")
        self.assertEqual(state['subdir']['1'], ['directory'],   "Subdirectory for version 1")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        
        # Delete the dataset TestSubmission-testdir
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")

    def testSymlinkFileUnpack(self):
        """Unpack zip file uploaded in a previous version to a new dataset - POST zip filename to /silo_name/items/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file testdir.zip, check response
        zipdata = self.uploadSubmissionZipfile(file_to_upload="testdir2.zip")
        # Upload zip file test, check response
        zipdata = self.uploadSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testdir"%self._endpointpath 
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access parent dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access new dataset, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getManifestUri("datasets/TestSubmission-testdir/")
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        # Access and check content of a resource
        (resp, filedata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="text/plain")
        checkdata = open("testdata/testdir/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        #Access state information of TestSubmission-testdir
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['currentversion'], '1', "Current version == 1")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 3, "List should contain manifest.rdf, test-csv.csv and testdir")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(state['subdir']['0'], [],   "Subdirectory for version 0")
        self.assertEqual(state['subdir']['1'], ['directory'],   "Subdirectory for version 1")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        # Delete the dataset TestSubmission-testdir
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")

    def testFileUploadToUnpackedDataset(self):
        """Upload a file to an unpacked dataset - POST filename to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testdir"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access and check list of contents in TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        # Access new dataset TestSubmission-testdir, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getManifestUri("datasets/TestSubmission-testdir/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        # Upload zip file to dataset TestSubmission-testdir
        fields = \
            [ ("filename", "testdir2.zip")
            ]
        zipdata = open("testdata/testdir2.zip").read()
        files = \
            [ ("file", "testdir2.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission-testdir/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testdir/testdir2.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access dataset TestSubmission-testdir, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getManifestUri("datasets/TestSubmission-testdir/")
        self.assertEqual(len(rdfgraph),18,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 3, "List should contain manifest.rdf, test-csv.csv and directory")
        self.assertEqual(len(state['files']['2']), 4, "List should contain manifest.rdf, test-csv.csv, directory and testdir2.zip")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(state['subdir']['0'], [],   "Subdirectory for version 0")
        self.assertEqual(state['subdir']['1'], ['directory'],   "Subdirectory for version 1")
        self.assertEqual(state['subdir']['2'], ['directory'],   "Subdirectory for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 6, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        self.assertEqual(len(parts['testdir2.zip'].keys()), 13, "File stats for testdir2.zip")
        # Delete the dataset TestSubmission-testdir
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")
        # Delete the dataset TestSubmission
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")

    def testUpdateUnpackedDataset(self):
        """Unpack zip file to an existing dataset - POST zip filename to /silo_name/items/dataset_name"""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadSubmissionZipfile()
        # Upload second zip file, check response
        zipdata = self.uploadSubmissionZipfile(file_to_upload="testdir2.zip")
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testdir"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access and check response for TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        # Access and check list of contents in TestSubmission-testdir
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getManifestUri("datasets/TestSubmission-testdir/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype = URIRef(oxds+"Grouping")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        # Unpack second ZIP file into dataset TestSubmission-testdir, check response
        fields = \
            [ ("filename", "testdir2.zip"),
              ("id", "TestSubmission-testdir")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=204, expect_reason="No Content") 
        # Access and check list of contents in TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),15,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((URIRef(base+"testdir2.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access dataset TestSubmission-testdir, check response
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testdir"))
        stype1 = URIRef("http://vocab.ox.ac.uk/dataset/schema#DataSet")
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getManifestUri("datasets/TestSubmission-testdir/")
        owl = "http://www.w3.org/2002/07/owl#"
        self.assertEqual(len(rdfgraph),22,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testdir2/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1/file1.c")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory2")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory2/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory2/file2.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 3, "List should contain manifest.rdf, directory and test-csv.csv")
        self.assertEqual(len(state['files']['2']), 4, "List should contain manifest.rdf, directory1, directory2 and test-csv.csv")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(state['subdir']['0'], [],   "Subdirectory count for version 0")
        self.assertEqual(state['subdir']['1'], ['directory'], "Subdirectory for version 1")
        self.assertEqual(len(state['subdir']['2']), 2, "Subdirectory for version 2 should be directory1 and directory2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 6, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        self.assertEqual(len(parts['directory1'].keys()), 0, "File stats for directory1")
        self.assertEqual(len(parts['directory2'].keys()), 0, "File stats for directory2")
        # Access dataset TestSubmission-testdir version 1
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/version1",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"1") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir version 1
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir/version1", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        # Access and check list of contents in TestSubmission-testdir version 0
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/version0",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype1) in rdfgraph, 'Testing submission type: '+subj+", "+stype1)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"0") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir version 0
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir/version0", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        # Access dataset TestSubmission-testdir version 2
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/version2",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        self.assertEqual(len(rdfgraph),22,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testdir2/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory1/file1.c")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory2")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory2/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory2/file2.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir version 2
        (resp, data) = self.doHTTP_GET(
            resource="states/TestSubmission-testdir/version2", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(len(state.keys()), 11, "States")
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '0', "Version 0")
        self.assertEqual(state['versions'][1], '1', "Version 1")
        self.assertEqual(state['versions'][2], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['0']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['1']), 3, "List should contain manifest.rdf, directory and test-csv.csv")
        self.assertEqual(len(state['files']['2']), 4, "List should contain manifest.rdf, directory1, directory2 and test-csv.csv")
        self.assertEqual(len(state['metadata_files']['0']), 0, "metadata_files of version 0")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(state['subdir']['0'], [],   "Subdirectory count for version 0")
        self.assertEqual(state['subdir']['1'], ['directory'], "Subdirectory for version 1")
        self.assertEqual(len(state['subdir']['2']), 2, "Subdirectory for version 2 should be directory1 and directory2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 6, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        self.assertEqual(len(parts['directory1'].keys()), 0, "File stats for directory1")
        self.assertEqual(len(parts['directory2'].keys()), 0, "File stats for directory2")
        # Delete the dataset TestSubmission-testdir
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")
        # Delete the dataset TestSubmission
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")

    def testMetadataMerging(self):
        """POST zipfile to /silo_name/items/dataset_name. Unpack zip file to a dataset.
        manifest.rdf located in unpacked zipfile is munged with existing manifest of the dataset."""
        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Submit ZIP file testdata/testrdf.zip, check response
        fields = []
        zipdata = open("testdata/testrdf.zip").read()
        files = \
            [ ("file", "testrdf.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/testrdf.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testrdf.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testrdf"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access parent dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in parent dataset - TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testrdf.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check list of contents in child dataset - TestSubmission-testrdf
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf"))
        base = self.getManifestUri("datasets/TestSubmission-testrdf/")
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"Grouping")        
        self.assertEqual(len(rdfgraph),21,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"arabic.txt")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        #Get the file arabic.txt
        (resp, arabic_data) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf/arabic.txt", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        #print type(arabic_data)
        #for s, p, o in rdfgraph.triples((None, URIRef(dcterms+"description"), None)):
        #    print s, p, type(o), '\n',  o
        #print '\n', '-'*50
        #print Literal(arabic_data)
        #print '\n', '-'*50
        #fr = open('testdata/testrdf/arabic.txt', 'r')
        #arabic_data = fr.read()
        #fr.close()
        #print '\n', '-'*50
        #print Literal(arabic_data)
        #print '\n', '-'*50
        #self.failUnless((subj,URIRef(dcterms+"description"),Literal(arabic_data)) in rdfgraph, 'dcterms:description')
        # Delete the dataset TestSubmission-testrdf
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testrdf", 
            expect_status="*", expect_reason="*")
        os.remove('response.xml')

    def testMetadataInDirectoryMerging(self):
        """POST zipfile to /silo_name/items/dataset_name. Unpack zip file to a dataset.
        manifest.rdf located within a folder in unpacked zipfile is munged with datsets existing manifest"""

        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Submit ZIP file testdata/testrdf2.zip, check response
        fields = []
        zipdata = open("testdata/testrdf2.zip").read()
        files = \
            [ ("file", "testrdf2.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/testrdf2.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testrdf2.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testrdf2"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access parent dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in parent dataset - TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testrdf2.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check list of contents in child dataset - TestSubmission-testrdf
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf2", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf2"))
        base = self.getManifestUri("datasets/TestSubmission-testrdf2/")
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"Grouping")
        self.assertEqual(len(rdfgraph),20,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2/test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        # Delete the dataset TestSubmission-testrdf2
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testrdf2", 
            expect_status="*", expect_reason="*")

    def testReferencedMetadataMerging(self):
        """POST zipfile to /silo_name/items/dataset_name. Unpack zip file to a dataset.
        manifest.rdf located within the unpacked zipfile is munged with datsets existing manifest.
        Also, manifest.rdf in the unpacked zipfile, references other metadata files, using the property rdfs:seeAlso.
        The metadata from these files are munged."""

        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Submit ZIP file testdata/testrdf3.zip, check response
        fields = []
        zipdata = open("testdata/testrdf3.zip").read()
        files = \
            [ ("file", "testrdf3.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/testrdf3.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testrdf3.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testrdf3"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access parent dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in parent dataset - TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        owl = "http://www.w3.org/2002/07/owl#"
        dc = "http://purl.org/dc/elements/1.1/"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testrdf3.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check list of contents in child dataset - TestSubmission-testrdf3
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf3", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        fr = open('response.xml', 'w')
        fr.write(rdfdata)
        fr.close()
        rdfgraph = Graph()
        rdfgraph.parse('response.xml', format='xml')
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf3"))
        subj2 = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf3/testrdf3/directory/hebrew.txt")) 
        base = self.getManifestUri("datasets/TestSubmission-testrdf3/")
        stype = URIRef(oxds+"Grouping")
        stype2 = URIRef(oxds+"item")
        self.assertEqual(len(rdfgraph),32,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset 3 with updated and merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/1a.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/1b.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/2a.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/3a.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/directory/hebrew.txt")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf3/test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/2aFiles/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(dc+"description"),"file1.a is another file") in rdfgraph, 'dc:description')
        self.failUnless((subj,URIRef(dc+"description"),"file1.b is another file") in rdfgraph, 'dc:description')
        self.failUnless((subj,URIRef(dc+"description"),"This is a archived test item 2a ") in rdfgraph, 'dc:description')

        self.failUnless((subj2,RDF.type,stype2) in rdfgraph, 'Testing submission type: '+subj2+", "+stype2)
        self.failUnless((subj2,URIRef(dcterms+"title"),"Hebrew text") in rdfgraph, 'dcterms:title')
        self.failUnless((subj2,URIRef(dcterms+"source"),"http://genizah.bodleian.ox.ac.uk/") in rdfgraph, 'dcterms:source')
        #Get the file hebrew.txt
        (resp, hebrew_data) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf3/testrdf3/directory/hebrew.txt", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        #self.failUnless((subj2,RDF.value,Literal(hebrew_data)) in rdfgraph, 'rdf:value')
        self.failUnless((subj2,RDF.value,None) in rdfgraph, 'rdf:value')
        # Delete the dataset TestSubmission-testrdf3
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testrdf3", 
            expect_status="*", expect_reason="*")

    def testReferencedMetadataMerging2(self):
        """POST zipfile to /silo_name/items/dataset_name. Unpack zip file to a dataset.
        manifest.rdf located within the unpacked zipfile is munged with datsets existing manifest.
        Also, manifest.rdf in the unpacked zipfile, references other metadata files, using the property rdfs:seeAlso.
        The metadata from these files are munged. One of the referenced files, references other files, which if they exists are also munged."""

        # Create a new dataset, check response
        self.createSubmissionDataset()
        # Submit ZIP file testdata/testrdf4.zip, check response
        fields = []
        zipdata = open("testdata/testrdf4.zip").read()
        files = \
            [ ("file", "testrdf4.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission/testrdf4.zip"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testrdf4.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        (resp,respdata) = self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        LHobtained = resp.getheader('Content-Location', None)
        LHexpected = "%sdatasets/TestSubmission-testrdf4"%self._endpointpath
        self.assertEquals(LHobtained, LHexpected, 'Content-Location not correct')
        # Access parent dataset, check response
        (resp, respdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in parent dataset - TestSubmission
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getManifestUri("datasets/TestSubmission"))
        base = self.getManifestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),13,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testrdf4.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check list of contents in child dataset - TestSubmission-testrdf3
        (resp, rdfdata) = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf4", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf4"))
        subj2 = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf4/testrdf4/directory/file1.a"))
        subj3 = URIRef(self.getManifestUri("datasets/TestSubmission-testrdf4/testrdf4/directory/file1.b"))
        base = self.getManifestUri("datasets/TestSubmission-testrdf4/")
        owl = "http://www.w3.org/2002/07/owl#"
        dc = "http://purl.org/dc/elements/1.1/"
        stype = URIRef(oxds+"Grouping")
        stype2 = URIRef(oxds+"item")
        self.assertEqual(len(rdfgraph),29,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory/1a.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory/1b.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/directory/2a.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf4/test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"mediator"),None) in rdfgraph, 'dcterms:mediator')
        self.failUnless((subj,URIRef(dcterms+"rights"),None) in rdfgraph, 'dcterms:rights')
        self.failUnless((subj,URIRef(dcterms+"license"),None) in rdfgraph, 'dcterms:license')
        self.failUnless((subj,URIRef(dcterms+"publisher"),None) in rdfgraph, 'dcterms:publisher')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dc+"description"),"This is a archived test item 2a ") in rdfgraph, 'dc:description')
        #self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset 4 with updated and merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test item 2a") in rdfgraph, 'dcterms:title')

        #self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("2aFiles")) in rdfgraph, 'dcterms:title')
        #for s, p, o in rdfgraph.triples((None, RDF.type, None)):
        #    print s, p, o, type(o)
        self.failUnless((subj2,RDF.type,stype2) in rdfgraph, 'Testing submission type: %s, %s'%(str(subj2), str(stype2)))
        self.failUnless((subj2,URIRef(dc+"description"),"This is a archived test item 1a ") in rdfgraph, 'dc:description')
        self.failUnless((subj2,URIRef(dcterms+"title"),"Test item 1a") in rdfgraph, 'dcterms:title')
        
        self.failUnless((subj3,RDF.type,stype2) in rdfgraph, 'Testing submission type: '+subj3+", "+stype2)
        self.failUnless((subj3,URIRef(dc+"description"),"This is test item 1b of type file") in rdfgraph, 'dc:description')
        self.failUnless((subj3,URIRef(dcterms+"title"),"Test item 1b") in rdfgraph, 'dcterms:title')
        
        # Delete the dataset TestSubmission-testrdf4
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testrdf4", 
            expect_status="*", expect_reason="*")

        # Delete the dataset TestSubmission
        resp = self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")

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
            , "testListSilos"
            , "testListDatasets"
            , "testSiloState"
            , "testDatasetNotPresent"
            , "testDatasetCreation"
            , "testDatasetCreation2"
            , "testDatasetRecreation"
            , "testDeleteDataset"
            , "testDatasetNaming"
            , "testDatasetStateInformation"
            , "testEmbargoOnCreation"
            , "testFileUpload"
            , "testFileDelete"
            , "testFileUpdate"
            , "testGetDatasetByVersion"
            , "testPostMetadataFile"
            , "testMetadataFileUpdate"
            , "testMetadataFileDelete"
            , "testPutCreateFile"
            , "testPutUpdateFile"
            , "testPutMetadataFile"
            , "testUnicodeMetadataFileUpdate"
            , "testDeleteEmbargo"
            , "testChangeEmbargo"
            , "testFileUnpack"
            , "testSymlinkFileUnpack"
            , "testMetadataMerging"
            , "testMetadataInDirectoryMerging"
            , "testFileUploadToUnpackedDataset"
            , "testUpdateUnpackedDataset"
            , "testReferencedMetadataMerging"
            , "testReferencedMetadataMerging2"
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
