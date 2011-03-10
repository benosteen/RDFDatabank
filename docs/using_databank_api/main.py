# Using the databank API

"""
Below is a guide on how to do HTTP GET, POST, PUT and DELETE in python.
To run the pyhon code here, you would also need the file datastore_link.py.

The full functionality of RDFDatabank is detailed in the API documentation at
http://databank.ora.ox.ac.uk/api 
https://github.com/anusharanganathan/RDFDatabank/tree/master/rdfdatabank/public/static/api_files
"""

import json as simplejson
from datastore_link import DatastoreLink

#--CONFIG-------------------------------------------------------
host = 'databank.ora.ox.ac.uk'
user_name = ''
password = ''
datastore = DatastoreLink(endpointhost=host)
datastore.setRequestUserPass(endpointuser=user_name, endpointpass=password)

#--HTTP GET-------------------------------------------------------
#Get a list of silos accessible to the user
(resp, respdata) = datastore.doHTTP_GET(resource="/silos", expect_type="application/JSON")
if resp.status >= 200 and resp.status < 300:
silos_list = simplejson.loads(respdata)

#--HTTP GET-------------------------------------------------------
#Get a list of all the datasets in the silo 'sandbox'
(resp, respdata) = datastore.doHTTP_GET(resource="/sandbox", expect_type="application/JSON")
if resp.status >= 200 and resp.status < 300:
dataset_list = simplejson.loads(respdata)

#--HTTP POST-------------------------------------------------------
#Create a new dataset 'TestSubmission' in the silo 'sandbox'
fields = [ 
("id", "TestSubmission")
]
files =[]
(reqtype, reqdata) = datastore.encode_multipart_formdata(fields, files)
(resp, respdata) = datastore.doHTTP_POST(reqdata, data_type=reqtype, resource="/sandbox/datsets", expect_type="application/JSON")
if resp.status >= 200 and resp.status < 300:                
    print resp.status, resp.reason
    print respdata

#--HTTP DELETE-------------------------------------------------------
#Delete the dataset 'TestSubmission' in the silo 'sandbox'
(resp, respdata) = datastore.doHTTP_DELETE(resource="/sandbox/datasets/TestSubmission")
print resp.status, resp.reason
print respdata

#--HTTP POST-------------------------------------------------------
#Upload file to dataset - POST file to dataset 'TestSubmission' in silo 'sandbox' (path is /sandbox/datasets/TestSubmission)
file_name="testdir.zip"
file_path="data/testdir.zip"
fields = []
zipdata = open(file_path).read()
files = [ 
    ("file", file_name, zipdata, "application/zip") 
]
(reqtype, reqdata) = datastore.encode_multipart_formdata(fields, files)
(resp, respdata) = datastore.doHTTP_POST(reqdata, data_type=reqtype, resource="/sandbox/datasets/TestSubmission", expect_type="application/JSON")
print resp.status, resp.reason
print respdata

#--HTTP PUT-------------------------------------------------------
#example metadata constructed in rdf. Add this metadata to the manifest (PUT this in manifest.rdf file)
metadata_content = """<rdf:RDF
  xmlns:dcterms='http://purl.org/dc/terms/'
  xmlns:oxds='http://vocab.ox.ac.uk/dataset/schema#'
  xmlns:ore='http://www.openarchives.org/ore/terms/'
  xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
>
  <oxds:DataSet rdf:about="http://example.org/testrdf/">
    <dcterms:title>Test dataset</dcterms:title>
    <dcterms:creator>Carl Sagan</dcterms:creator>
    <dcterms:abstract>abstract</dcterms:abstract>
  </oxds:DataSet>
</rdf:RDF>"""

(resp, respdata) = datastore.doHTTP_PUT(metadata_content, resource="sandbox/datasets/TestSubmission/manifest.rdf", expect_type="text/plain")
print resp.status, resp.reason
print respdata

#---------------------------------------------------------
