#!/usr/bin/python
# $Id: $
"""
Define configuration for RDFDatabank testing

$Rev: $
"""

class RDFDatabankConfig:

    granary_uri_root="http://dataflow-jenkins.bodleian.ox.ac.uk"
    
    # Access to local test VM
    endpointhost="localhost:5000"

    #endpointpath="/sandbox/"
    endpointpath="/test/"
    endpointpath2="/test2/"

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

# End.
