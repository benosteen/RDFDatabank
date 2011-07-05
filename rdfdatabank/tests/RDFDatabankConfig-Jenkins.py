#!/usr/bin/python
# $Id: $
"""
Define configuration for RDFDatabank testing

$Rev: $
"""

class RDFDatabankConfig:

    granary_uri_root="http://dataflow-jenkins.bodleian.ox.ac.uk"

    # Access via IP address
    #endpointhost="databank.ora.ox.ac.uk"
    #Access to local dev VM
    endpointhost="dataflow-jenkins.bodleian.ox.ac.uk"
 
    # Access credentials for testing
    endpointpath="/sandbox/"

    # Access credentials for testing from local dev VM as user
    endpointuser="sandbox_user"
    endpointpass="sandbox"
    
    # Access credentials for testing from local dev VM as admin
    endpointadminuser="admin"
    endpointadminpass="test"

    # Later, may define methods to override these defaults, e.g. from a configuration file

# End.
