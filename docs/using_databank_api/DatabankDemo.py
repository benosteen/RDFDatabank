#-*- coding: utf-8 -*-
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

#Databank API demo

import urllib2
import base64
import urllib
from multipartform import MultiPartForm

#===============================================================================
#Using urllib2 to create a package in Databank
url = "http://databank-vm1.oerc.ox.ac.uk/test/datasets"
req = urllib2.Request(url)
USER = "admin"
PASS = "test"
identifier = "TestSubmission"
auth = 'Basic ' + base64.urlsafe_b64encode("%s:%s" % (USER, PASS))
req.add_header('Authorization', auth)
req.add_header('Accept', 'application/JSON')
req.add_data(urllib.urlencode({'id': identifier}))

# To verify the method is POST
req.get_method()

ans = urllib2.urlopen(req)

ans.read()
ans.msg
ans.code

#===============================================================================
#Using urllib2 to post a file in Databank
#Add a file
form = MultiPartForm()
filename = "solrconfig.xml"
filepath = "./solrconfig.xml"
form.add_file('file', filename, fileHandle=open(filepath))

# Build the request
url2 = "http://databank-vm1.oerc.ox.ac.uk/test/datasets/TestSubmission"
req2 = urllib2.Request(url2)
auth = 'Basic ' + base64.urlsafe_b64encode("admin:test")
req2.add_header('Authorization', auth)
req2.add_header('Accept', 'application/JSON')
body = str(form)
req2.add_header('Content-type', form.get_content_type())
req2.add_header('Content-length', len(body))
req2.add_data(body)

print
print 'OUTGOING DATA:'
print req2.get_data()
ans2 = urllib2.urlopen(req2)
print
print 'SERVER RESPONSE:'
ans2.read()