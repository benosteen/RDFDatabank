#!/usr/bin/python
# $Id: $
"""
Define configuration for RDFDatabank testing

$Rev: $
"""

class RDFDatabankConfig:

    granary_uri_root="http://databank.ora.ox.ac.uk"

    # Access via IP address
    #endpointhost="192.168.23.133"  #Access to local dev VM
    endpointhost="databank.ora.ox.ac.uk"
    endpointpath="/sandbox/"

    endpointadminuser="admin"
    endpointadminpass="test"
    
    # Access credentials for testing from local dev VM
    endpointuser="admin"
    endpointpass="test"

    # Later, may define methods to override these defaults, e.g. from a configuration file

# End.
