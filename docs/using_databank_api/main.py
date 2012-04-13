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

# Using the databank API

"""
Below is a guide on how to do HTTP GET, POST, PUT and DELETE in python.
To run the pyhon code here, you would also need the file HTTP_request.py.

The full functionality of RDFDatabank is detailed in the API documentation at
http://databank.ora.ox.ac.uk/api 
https://github.com/dataflow/RDFDatabank/tree/master/rdfdatabank/public/static/api_files
"""

import json as simplejson
from lib.HTTP_request import HTTPRequest

#--CONFIG-------------------------------------------------------
host = 'databank-vm1.oerc.ox.ac.uk'
user_name = 'admin'
password = 'test'
datastore = HTTPRequest(endpointhost=host)
datastore.setRequestUserPass(endpointuser=user_name, endpointpass=password)

#--HTTP GET-------------------------------------------------------
#Get a list of silos accessible to the user
(resp, respdata) = datastore.doHTTP_GET(resource="/silos", expect_type="application/JSON")
print "Get list of silos"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    silos_list = simplejson.loads(respdata)
    print "number of silos", len(silos_list)
print "-"*40, "\n\n"

#--HTTP GET-------------------------------------------------------
#Get a list of all the datasets in the silo 'sandbox'
(resp, respdata) = datastore.doHTTP_GET(resource="/sandbox", expect_type="application/JSON")
print "Get list of datasets"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    dataset_list = simplejson.loads(respdata)
    print "number of datasets", len(dataset_list.keys())
else:
    print "Error getting list of datasets"
print "-"*40, "\n\n"

#--HTTP DELETE-------------------------------------------------------
#Delete the dataset 'TestSubmission' in the silo 'sandbox'
(resp, respdata) = datastore.doHTTP_DELETE(resource="/sandbox/datasets/TestSubmission")
print "deleting dataset"
print resp.status, resp.reason
print respdata
print "-"*40, "\n\n"

#--HTTP POST-------------------------------------------------------
#Create a new dataset 'TestSubmission' in the silo 'sandbox'
fields = [ 
    ("id", "TestSubmission")
]
files =[]
(reqtype, reqdata) = datastore.encode_multipart_formdata(fields, files)
(resp, respdata) = datastore.doHTTP_POST(reqdata, data_type=reqtype, resource="/sandbox/datasets", expect_type="application/JSON")
print "Create new dataset"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    print respdata
else:
    print "Error creating dataset"
print "-"*40, "\n\n"

#--HTTP POST-------------------------------------------------------
#Upload file to dataset - POST file to dataset 'TestSubmission' in silo 'sandbox' (path is /sandbox/datasets/TestSubmission)
file_name="testrdf4.zip"
file_path="data/testrdf4.zip"
fields = []
zipdata = open(file_path).read()
files = [ 
    ("file", file_name, zipdata, "application/zip") 
]
(reqtype, reqdata) = datastore.encode_multipart_formdata(fields, files)
(resp, respdata) = datastore.doHTTP_POST(reqdata, data_type=reqtype, resource="/sandbox/datasets/TestSubmission", expect_type="application/JSON")
print "Post file testrdf4.zip to dataset"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    print respdata
else:
    print "Error posting file to dataset"
print "-"*40, "\n\n"

#--HTTP POST-------------------------------------------------------
#Upload file to dataset and test munging. POST file to dataset 'TestSubmission' in silo 'sandbox' (path is /sandbox/datasets/TestSubmission)
#file_name="unicode07.xml"
file_name="manifest.rdf"
file_path="data/unicode07.xml"
fields = []
zipdata = open(file_path).read()
files = [ 
    ("file", file_name, zipdata, "application/rdf+xml") 
]
(reqtype, reqdata) = datastore.encode_multipart_formdata(fields, files)
(resp, respdata) = datastore.doHTTP_POST(reqdata, data_type=reqtype, resource="/sandbox/datasets/TestSubmission", expect_type="application/JSON")
print "Post file unicode07.xml to dataset"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    print respdata
else:
    print "Error posting file to dataset"
print "-"*40, "\n\n"

#--HTTP PUT-------------------------------------------------------
#example metadata constructed in rdf. Add this metadata to the manifest (PUT this in manifest.rdf file)
metadata_content = """<rdf:RDF
  xmlns:dcterms='http://purl.org/dc/terms/'
  xmlns:oxds='http://vocab.ox.ac.uk/dataset/schema#'
  xmlns:ore='http://www.openarchives.org/ore/terms/'
  xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
>
  <oxds:DataSet rdf:about="http://example.org/testrdf.zip">
    <dcterms:title>Test dataset</dcterms:title>
    <dcterms:creator>Carl Sagan</dcterms:creator>
    <dcterms:abstract>abstract</dcterms:abstract>
  </oxds:DataSet>
</rdf:RDF>"""

(resp, respdata) = datastore.doHTTP_PUT(metadata_content, resource="/sandbox/datasets/TestSubmission/manifest.rdf", expect_type="text/plain")
print "Putting manifest data into dataset"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    print respdata
else:
    print "Error putting manifest data into dataset"
print "-"*40, "\n\n"

#--HTTP POST-------------------------------------------------------
#Unpack zip file in dataset
file_name="testrdf4.zip"
fields = []
fields = [ 
    ("filename", "testrdf4.zip"),
    ("id", "TestSubmission")
]
zipdata = open(file_path).read()
files = []
(reqtype, reqdata) = datastore.encode_multipart_formdata(fields, files)
(resp, respdata) = datastore.doHTTP_POST(reqdata, data_type=reqtype, resource="/sandbox/items/TestSubmission", expect_type="application/JSON")
print "Post file testrdf4.zip to dataset for unpacking"
print resp.status, resp.reason
if resp.status >= 200 and resp.status < 300:
    print respdata
else:
    print "Error unpacking file to dataset"
print "-"*40, "\n\n"

#---------------------------------------------------------

