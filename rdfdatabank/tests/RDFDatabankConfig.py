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
Define configuration for RDFDatabank testing
"""

class RDFDatabankConfig:

    granary_uri_root="http://databank"
    
    # Access via IP address
    endpointhost="localhost"
    endpointpath="/sandbox/"
    endpointpath2="/sandbox2/"

    endpointuser="sandbox_user"
    endpointpass="sandbox"

    #Admin1 of silo1
    endpointadminuser="admin"
    endpointadminpass="test"
    #Admin2 of silo1
    endpointadminuser2="admin2"
    endpointadminpass2="test2"
    #Admin3 of silo2
    endpointadminuser3="admin3"
    endpointadminpass3="test3"

    #Manager1 of silo1
    endpointmanageruser="sandbox_manager"
    endpointmanagerpass="managertest"
    #Manager2 of silo1
    endpointmanageruser2="sandbox_manager2"
    endpointmanagerpass2="managertest2"
    #Manager3 of silo2
    endpointmanageruser3="sandbox_manager3"
    endpointmanagerpass3="managertest3"

    #Submitter1 of silo1
    endpointsubmitteruser="sandbox_user"
    endpointsubmitterpass="sandbox"
    #Submitter2 of silo1
    endpointsubmitteruser2="sandbox_user2"
    endpointsubmitterpass2="sandbox2"
    #Submitter3 of silo2
    endpointsubmitteruser3="sandbox_user3"
    endpointsubmitterpass3="sandbox3"

    #Access credentials for generic user
    endpointgeneraluser = ""
    endpointgeneralpass = ""

    # Later, may define methods to override these defaults, e.g. from a configuration file

# End.
