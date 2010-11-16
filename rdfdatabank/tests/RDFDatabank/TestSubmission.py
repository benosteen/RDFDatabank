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
#My system is running rdflib version 2.4.2. So adding rdflib v3.0 to sys path
rdflib_path = os.path.join(os.getcwd(), 'rdflib')
sys.path.insert(0, rdflib_path)
import rdflib
from rdflib.namespace import RDF
from rdflib.graph import Graph
from rdflib.plugins.memory import Memory
from StringIO import StringIO
from rdflib import URIRef
from rdflib import Literal
rdflib.plugin.register('sparql',rdflib.query.Processor,'rdfextras.sparql.processor','Processor')
rdflib.plugin.register('sparql', rdflib.query.Result,
                       'rdfextras.sparql.query', 'SPARQLQueryResult')

if __name__ == "__main__":
    # For testing: 
    # add main library directory to python path if running stand-alone
    sys.path.append("..")

from MiscLib import TestUtils
from TestLib import SparqlQueryTestCase

from RDFDatabankConfig import RDFDatabankConfig

logger = logging.getLogger('TestSubmission')

class TestSubmission(SparqlQueryTestCase.SparqlQueryTestCase):
    """
    Test simple dataset submissions to RDFDatabank
    """
    def setUp(self):
        #super(TestSubmission, self).__init__()
        self.setRequestEndPoint(
            endpointhost=RDFDatabankConfig.endpointhost,  # Via SSH tunnel
            endpointpath=RDFDatabankConfig.endpointpath)
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointuser,
            endpointpass=RDFDatabankConfig.endpointpass)
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")
        return

    def tearDown(self):
        return

    # Create empty test submission dataset
    def createTestSubmissionDataset(self):
        # Create a new dataset, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        return

    def uploadTestSubmissionZipfile(self, file_to_upload="testdir.zip"):
        # Submit ZIP file, check response
        fields = []
        zipdata = open("data/%s"%file_to_upload).read()
        files = \
            [ ("file", file_to_upload, zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        return zipdata

    def updateTestSubmissionZipfile(self, file_to_upload="testdir.zip", filename=None):
        # Submit ZIP file, check response
        fields = []
        if filename:
            fields = \
                [ ("filename", filename)
                ]
        zipdata = open("data/%s"%file_to_upload).read()
        files = \
            [ ("file", file_to_upload, zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=204, expect_reason="No Content")
        return zipdata

    # Actual tests follow
    def testListSilos(self):
        """List all silos your account has access to - GET /silo"""
        #Write a test to list all the silos. Test to see if it returns 200 OK and the list of silos is not empty
        # Access list silos, check response
        data = self.doHTTP_GET(
            endpointpath=None,
            resource="/silos/", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # check list of silos is not empty
        self.failUnless(len(data)>0, "No silos returned")
   
    def testListDatasets(self):
        """List all datasets in a silo - GET /silo_name/datasets"""
        # Access list of datasets in the silo, check response
        data = self.doHTTP_GET(
            resource="datasets/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Save initial list of datasets
        datasetlist = []
        for k in data:
            datasetlist.append(k)
        # Create a new dataset
        self.createTestSubmissionDataset()
        # Read list of datasets, check that new list is original + new dataset
        data = self.doHTTP_GET(
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
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # read list of datasets, check result is same as original list
        data = self.doHTTP_GET(
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
        data = self.doHTTP_GET(
            resource="states/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # check silo name and base_uri
        silo_name = RDFDatabankConfig.endpointpath.strip('/')
        silo_base = 'http://%s%sdatasets/'%(RDFDatabankConfig.endpointhost, RDFDatabankConfig.endpointpath)
        self.assertEqual(data['silo'], silo_name, 'Silo name is %s not %s' %(data['silo'], silo_name))
        self.assertEqual(data['uri_base'], silo_base, 'Silo uri_base is %s not %s' %(data['uri_base'], silo_base))
        self.failUnless(len(data['datasets'])>0, "No datasets returned")
        # Save initial list of datasets
        datasetlist = data['datasets']
        # Create a new dataset
        self.createTestSubmissionDataset()
        # Read list of datasets, check that new list is original + new dataset
        data = self.doHTTP_GET(
            resource="states/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        newlist = data['datasets']
        logger.debug("Orig. length "+str(len(datasetlist))+", new length "+str(len(newlist)))
        self.assertEquals(len(newlist), len(datasetlist)+1, "One additional dataset")
        for ds in datasetlist: self.failUnless(ds in newlist, "Dataset "+ds+" in original list, not in new list")
        for ds in newlist: self.failUnless((ds in datasetlist) or (ds == "TestSubmission"), "Datset "+ds+" in new list, not in original list")
        self.failUnless("TestSubmission" in newlist, "testSubmission in new list")
        # Delete new dataset
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # read list of datasets, check result is same as original list
        data = self.doHTTP_GET(
            resource="states/", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        newlist = data['datasets']
        logger.debug("Orig. length "+str(len(datasetlist))+", new length "+str(len(newlist)))
        self.assertEquals(len(newlist), len(datasetlist), "Back to original content in silo")
        for ds in datasetlist: self.failUnless(ds in newlist, "Datset "+ds+" in original list, not in new list")
        for ds in newlist: self.failUnless(ds in datasetlist, "Datset "+ds+" in new list, not in original list")

    def testDatasetNotPresent(self):
        """Verify dataset is not present - GET /silo_name/dataset_name"""
        self.doHTTP_GET(resource="TestSubmission", expect_status=404, expect_reason="Not Found")

    def testDatasetCreation(self):
        """Create dataset - POST id to /silo_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Access dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')

    def testDatasetCreation2(self):
        """Create dataset - POST to /silo_name/dataset_name"""
        # Create a new dataset, check response
        fields = []
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=201, expect_reason="Created")
        # Access dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')

    def testDatasetRecreation(self):
        """Create dataset - POST existing id to /silo_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Access dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        #Recreate the dataset, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets",
            expect_status=409, expect_reason="Conflict: Dataset Already Exists")
        #Recreate the dataset, check response
        fields = []
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=403, expect_reason="Forbidden")
        # Access dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))

    def testDeleteDataset(self):
        """Delete dataset - DELETE /silo_name/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Delete dataset, check response
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")

    def testDatasetNaming(self):
        """Create dataset - POST to /silo_name/dataset_name. If name is valid, return 201, else return 403"""
        names = [("TestSubmission-1", 201, "Created")
            ,("TestSubmission_2", 201, "Created")
            ,("TestSubmission:3", 201, "Created")
            ,("TestSubmission*4", 403, "Forbidden")
            ,("TestSubmission/5", 404, "Not Found")
            ,("TestSubmission\6", 403, "Forbidden")
            ,("TestSubmission,7", 403, "Forbidden")
            ,("TestSubmission&8", 403, "Forbidden")
            ,("TestSubmission.9", 403, "Forbidden")
            ,("""Test"Submission""", 403, "Forbidden")
            ,("Test'Submission", 403, "Forbidden")
            #,("Test Submission", 403, "Forbidden") #This is being posted as 'Test' - Why?
            ,("TestSubmission$", 403, "Forbidden")
        ]
        fields = []
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        for name, status, reason in names:
            #Create a new dataset, check response
            self.doHTTP_POST(
                reqdata, reqtype, 
                resource="datasets/%s"%name, 
                expect_status=status, expect_reason=reason)
            # Access dataset, check response
            if status == 201:
                rdfdata = self.doHTTP_GET(
                    resource="datasets/%s"%name, 
                    expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
                rdfgraph = Graph()
                rdfstream = StringIO(rdfdata)
                rdfgraph.parse(rdfstream) 
                self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
            elif status == 403:
                rdfdata = self.doHTTP_GET(
                    resource="datasets/%s"%name, 
                    expect_status=404, expect_reason="Not Found")
        #Delete Datasets
        for name, status, reason in names:
            if not status == 201:
                continue
            self.doHTTP_DELETE(
                resource="datasets/%s"%name, 
                expect_status=200, expect_reason="OK")

    def testDatasetStateInformation(self):
        """Get state information of dataset - GET /silo_name/states/dataset_name."""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Access state info
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 1, "Initially one version")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['currentversion'], '1', "Current version == 1")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(state['files']['1'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        # date
        # version_dates
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testFileUpload(self):
        """Upload file to dataset - POST file to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        #Access state information
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        #TODO: The files of version 1 are also being updated - correct this
        #self.assertEqual(state['files']['1'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testFileDelete(self):
        """Delete file in dataset - DELETE /silo_name/datasets/dataset_name/file_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        # Access and check zip file content and version
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        # Delete file, check response
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission/testdir.zip", 
            expect_status=200, expect_reason="OK")
        # Access and check zip file does not exist
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=404, expect_reason="Not Found")
       # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),8,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['3']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testFileUpdate(self):
        """POST file to dataset twice - POST file to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response (uploads the file testdir.zip)
        zipdata = self.uploadTestSubmissionZipfile()
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission")) 
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        # Access and check zip file content and version
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        # Upload zip file again, check response
        zipdata = self.updateTestSubmissionZipfile(file_to_upload="testdir2.zip", filename="testdir.zip")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')  
        # Access and check zip file content
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['3']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testMetadataFileUpdate(self):
        """POST manifest to dataset - POST manifest.rdf to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload metadata file, check response
        zipdata = self.updateTestSubmissionZipfile(file_to_upload="manifest.rdf")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        # Update metadata file, check response
        zipdata = self.updateTestSubmissionZipfile(file_to_upload="manifest2.rdf", filename="manifest.rdf")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),'Test dataset with updated and merged metadata') in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['3']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testMetadataFileDelete(self):
        """Delete manifest in dataset - DELETE /silo_name/datasets/dataset_name/manifest.rdf"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Delete metadata file, check response
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=403, expect_reason="Forbidden")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        dcterms = "http://purl.org/dc/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'1') in rdfgraph, 'oxds:currentVersion')

    def testPutCreateFile(self):
        """PUT file contents to new filename - PUT file contents to /silo_name/datasets/dataset_name/file_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Put zip file, check response
        zipdata = open("data/testdir.zip").read()       
        self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/testdir.zip", 
            expect_status=201, expect_reason="Created", expect_type="*/*")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check zip file content
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        #TODO: The files of version 1 are also being updated - correct this
        #self.assertEqual(state['files']['1'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testPutUpdateFile(self):
        """PUT file contents to existing filename - PUT file contents to /silo_name/datasets/dataset_name/file_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Put zip file, check response
        zipdata = open("data/testdir.zip").read()       
        self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/testdir.zip", 
            expect_status=201, expect_reason="Created", expect_type="*/*")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission")) 
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        # Access and check zip file content and version
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        # Put zip file again, check response
        zipdata = open("data/testdir2.zip").read()       
        self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/testdir.zip", 
            expect_status=204, expect_reason="No Content", expect_type="*/*")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')  
        # Access and check zip file content
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        #self.assertEqual(state['files']['1'], ['manifest.rdf'], "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['files']['3']), 2, "List should contain manifest.rdf and testdir.zip")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir.zip'].keys()), 13, "File stats for testdir.zip")

    def testPutMetadataFile(self):
        """Add metadata to manifest - PUT metadata to /silo_name/datasets/dataset_name/manifest.rdf"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Put manifest file, check response
        zipdata = open("data/manifest.rdf").read()       
        self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="*/*")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"        
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        # Update metadata file, check response
        zipdata = open("data/manifest2.rdf").read()       
        self.doHTTP_PUT(zipdata, resource="datasets/TestSubmission/manifest.rdf", 
            expect_status=204, expect_reason="No Content", expect_type="*/*")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'3') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"title"),'Test dataset with updated and merged metadata') in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['3']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(len(state['subdir']['1']), 0,   "Subdirectory count for version 1")
        self.assertEqual(len(state['subdir']['2']), 0,   "Subdirectory count for version 2")
        self.assertEqual(len(state['subdir']['3']), 0,   "Subdirectory count for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 3, "Parts")
        self.assertEqual(len(parts['4=TestSubmission'].keys()), 13, "File stats for 4=TestSubmission")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")

    def testDeleteEmbargo(self):
        """Delete embargo information - POST embargo_change to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        #Access dataset and check content
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        # Delete embargo, check response
        fields = \
            [ ("embargo_change", 'true')
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'False') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], False, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], "", "Should have no date for embargoed_until")
        
    def testChangeEmbargo(self):
        """Modify embargo information - POST embargo_change, embargo, embargo_until to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        #Access dataset and check content
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),7,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        # Delete embargo, check response
        d = datetime.now()
        delta = timedelta(days=365*3)
        d2 = d + delta
        d2 = d2.isoformat()
        fields = \
            [ ("embargo_change", 'true')
             ,("embargoed", 'true')
             ,("embargoed_until", d2)
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission", 
            expect_status=204, expect_reason="Updated")
        #Access dataset and check content
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),8,'Graph length %i' %len(rdfgraph))
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        dcterms = "http://purl.org/dc/terms/"
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef(oxds+"DataSet")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),'True') in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),d2) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        #Access state information and check
        data = self.doHTTP_GET(
            resource="states/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(state['metadata']['embargoed_until'], d2, "embargoed_until?")

    def testFileUnpack(self):
        """Unpack zip file to a new dataset - POST zip filename to /silo_name/items/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Access parent dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access new dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
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
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        # Access and check content of a resource
        filedata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="*/*")
        checkdata = open("data/testdir/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        #Access state information of TestSubmission-testdir
        data = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 3, "List should contain manifest.rdf, testdir and test-csv.csv")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(state['subdir']['1'], [],   "Subdirectory for version 1")
        self.assertEqual(state['subdir']['2'], ['directory'],   "Subdirectory for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        
        # Delete the dataset TestSubmission-testdir
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")

    def testSymlinkFileUnpack(self):
        """Unpack zip file uploaded in a previous version to a new dataset - POST zip filename to /silo_name/items/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file testdir.zip, check response
        zipdata = self.uploadTestSubmissionZipfile(file_to_upload="testdir2.zip")
        # Upload zip file test, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Access parent dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"3") in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access new dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
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
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        # Access and check content of a resource
        filedata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="*/*")
        checkdata = open("data/testdir/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        #Access state information of TestSubmission-testdir
        data = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 2, "Two versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 3, "List should contain manifest.rdf, test-csv.csv and testdir")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(state['subdir']['1'], [],   "Subdirectory for version 1")
        self.assertEqual(state['subdir']['2'], ['directory'],   "Subdirectory for version 2")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 5, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        # Delete the dataset TestSubmission-testdir
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")

    def testFileUploadToUnpackedDataset(self):
        """Upload a file to an unpacked dataset - POST filename to /silo_name/datasets/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Access and check list of contents in TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        # Access new dataset TestSubmission-testdir, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
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
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        # Upload zip file to dataset TestSubmission-testdir
        fields = \
            [ ("filename", "testdir2.zip")
            ]
        zipdata = open("data/testdir2.zip").read()
        files = \
            [ ("file", "testdir2.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission-testdir/", 
            expect_status=201, expect_reason="Created")
        # Access dataset TestSubmission-testdir, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        self.assertEqual(len(rdfgraph),15,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
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
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"3") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir
        data = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        #TODO: Uploading a file also changes the file information for the previous version - correct this
        #self.assertEqual(len(state['files']['2']), 3, "List should contain manifest.rdf, test-csv.csv and directory")
        self.assertEqual(len(state['files']['3']), 4, "List should contain manifest.rdf, test-csv.csv, directory and testdir2.zip")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(state['subdir']['1'], [],   "Subdirectory for version 1")
        self.assertEqual(state['subdir']['2'], ['directory'],   "Subdirectory for version 2")
        self.assertEqual(state['subdir']['3'], ['directory'],   "Subdirectory for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 6, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['directory'].keys()), 0, "File stats for directory")
        self.assertEqual(len(parts['test-csv.csv'].keys()), 13, "File stats for test-csv.csv")
        self.assertEqual(len(parts['testdir2.zip'].keys()), 13, "File stats for testdir2.zip")
        # Delete the dataset TestSubmission-testdir
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")
        # Delete the dataset TestSubmission
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")

    def testUpdateUnpackedDataset(self):
        """Unpack zip file to an existing dataset - POST zip filename to /silo_name/items/dataset_name"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Upload second zip file, check response
        zipdata = self.uploadTestSubmissionZipfile(file_to_upload="testdir2.zip")
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Access and check list of contents in TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),11,'Graph length %i' %len(rdfgraph))
        # Access new dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        self.assertEqual(len(rdfgraph),14,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
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
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"2") in rdfgraph, 'oxds:currentVersion')
        # Unpack second ZIP file into dataset TestSubmission-testdir, check response
        fields = \
            [ ("filename", "testdir2.zip"),
              ("id", "TestSubmission-testdir")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created") 
        # Access and check list of contents in TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((URIRef(base+"testdir2.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"3") in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access dataset TestSubmission-testdir, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream)
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        owl = "http://www.w3.org/2002/07/owl#"
        self.assertEqual(len(rdfgraph),18,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testdir2/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file1.c")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(oxds+"currentVersion"),"3") in rdfgraph, 'oxds:currentVersion')
        #Access state information of TestSubmission-testdir
        data = self.doHTTP_GET(
            resource="states/TestSubmission-testdir", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'], "TestSubmission-testdir", "Submission item identifier")
        self.assertEqual(len(state['versions']), 3, "Three versions")
        self.assertEqual(state['versions'][0], '1', "Version 1")
        self.assertEqual(state['versions'][1], '2', "Version 2")
        self.assertEqual(state['versions'][2], '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'], 'xml', "RDF file type")
        self.assertEqual(state['rdffilename'], 'manifest.rdf', "RDF file name")
        self.assertEqual(len(state['files']['1']), 1, "List should contain just manifest.rdf")
        self.assertEqual(len(state['files']['2']), 3, "List should contain manifest.rdf, directory and test-csv.csv")
        self.assertEqual(len(state['files']['3']), 2, "List should contain manifest.rdf and testdri2")
        self.assertEqual(len(state['metadata_files']['1']), 0, "metadata_files of version 1")
        self.assertEqual(len(state['metadata_files']['2']), 0, "metadata_files of version 2")
        self.assertEqual(len(state['metadata_files']['3']), 0, "metadata_files of version 3")
        self.assertEqual(state['subdir']['1'], [],   "Subdirectory count for version 1")
        self.assertEqual(state['subdir']['2'], ['directory'],   "Subdirectory for version 2")
        self.assertEqual(state['subdir']['3'], ['testdir2'],   "Subdirectory for version 3")
        self.assertEqual(state['metadata']['createdby'], RDFDatabankConfig.endpointuser, "Created by")
        self.assertEqual(state['metadata']['embargoed'], True, "Embargoed?")
        self.assertEqual(len(parts.keys()), 4, "Parts")
        self.assertEqual(len(parts['4=TestSubmission-testdir'].keys()), 13, "File stats for 4=TestSubmission-testdir")
        self.assertEqual(len(parts['manifest.rdf'].keys()), 13, "File stats for manifest.rdf")
        self.assertEqual(len(parts['testdir2'].keys()), 0, "File stats for testdir2")
        # Delete the dataset TestSubmission-testdir
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testdir", 
            expect_status="*", expect_reason="*")
        # Delete the dataset TestSubmission
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")

    def testMetadataMerging(self):
        """Unpack zip file to a dataset - POST zip filename to /silo_name/items/dataset_name
        manifest.rdf in zipfile is munged with datsets existing manifest"""
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Submit ZIP file data/testrdf.zip, check response
        fields = []
        zipdata = open("data/testrdf.zip").read()
        files = \
            [ ("file", "testrdf.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testrdf.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Access parent dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in parent dataset - TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testrdf.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check list of contents in child dataset - TestSubmission-testrdf
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testrdf"))
        base = self.getRequestUri("datasets/TestSubmission-testrdf/")
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"Grouping")
        self.assertEqual(len(rdfgraph),16,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        #self.failUnless((URIRef("http://example.org/testrdf/"),URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        #self.failUnless((URIRef("http://example.org/testrdf/"),RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"test-csv.csv")) in rdfgraph)
        #self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/manifest.rdf")) in rdfgraph)
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        # Delete the dataset TestSubmission-testrdf
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testrdf", 
            expect_status="*", expect_reason="*")

    def testMetadataInDirectoryMerging(self):
        """Unpack zip file to a dataset - POST zip filename to /silo_name/items/dataset_name
        manifest.rdf from within a folder in unpacked zipfile is munged with datsets existing manifest"""

        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Submit ZIP file data/testrdf2.zip, check response
        fields = []
        zipdata = open("data/testrdf2.zip").read()
        files = \
            [ ("file", "testrdf2.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testrdf2.zip")
            ]
        files = []
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        #TODO: TEST FOR LOCATION HEADER
        # Access parent dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/json")
        # Access and check list of contents in parent dataset - TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        base = self.getRequestUri("datasets/TestSubmission/")
        dcterms = "http://purl.org/dc/terms/"
        ore  = "http://www.openarchives.org/ore/terms/"
        oxds = "http://vocab.ox.ac.uk/dataset/schema#"
        stype = URIRef(oxds+"DataSet")
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testrdf2.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testrdf2.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        self.failUnless((subj,URIRef(dcterms+"identifier"),None) in rdfgraph, 'dcterms:identifier')
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        # Access and check list of contents in child dataset - TestSubmission-testrdf
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testrdf2", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testrdf2"))
        base = self.getRequestUri("datasets/TestSubmission-testrdf2/")
        owl = "http://www.w3.org/2002/07/owl#"
        stype = URIRef(oxds+"Grouping")
        self.assertEqual(len(rdfgraph),17,'Graph length %i' %len(rdfgraph))
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
        self.failUnless((subj,URIRef(dcterms+"creator"),None) in rdfgraph, 'dcterms:creator')
        self.failUnless((subj,URIRef(oxds+"isEmbargoed"),None) in rdfgraph, 'oxds:isEmbargoed')
        self.failUnless((subj,URIRef(oxds+"embargoedUntil"),None) in rdfgraph, 'oxds:embargoedUntil')
        self.failUnless((subj,URIRef(dcterms+"created"),None) in rdfgraph, 'dcterms:created')
        self.failUnless((subj,URIRef(oxds+"currentVersion"),'2') in rdfgraph, 'oxds:currentVersion')
        # Delete the dataset TestSubmission-testrdf2
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission-testrdf2", 
            expect_status="*", expect_reason="*")

    # Sentinel/placeholder tests

    def testUnits(self):
        assert (True)

    def testComponents(self):
        assert (True)

    def testIntegration(self):
        assert (True)

    def testPending(self):
        #Need to return location headers for 201
        #Need to fix bug - state information of the previous verison is updated on file upload
        #Need to have performance tests and analyse performance
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
            , "testFileUpload"
            , "testFileDelete"
            , "testFileUpdate"
            , "testMetadataFileUpdate"
            , "testMetadataFileDelete"
            , "testPutCreateFile"
            , "testPutUpdateFile"
            , "testPutMetadataFile"
            , "testDeleteEmbargo"
            , "testChangeEmbargo"
            , "testFileUnpack"
            , "testSymlinkFileUnpack"
            , "testMetadataMerging"
            , "testMetadataInDirectoryMerging"
            , "testFileUploadToUnpackedDataset"
            , "testUpdateUnpackedDataset"
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
