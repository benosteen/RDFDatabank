#!/usr/bin/python
# $Id: $
"""
Define configuration for RDFDatabank testing

$Rev: $
"""

class RDFDatabankConfig:

    # Access via SSH tunnel
    endpointhost="localhost:9080"
    endpointpath="/admiral-test/packages/"

    # Access via IP address
    endpointhost="163.1.127.173"
    endpointpath="/admiral-test/"

    # Access credentials for testing
    endpointuser="admiral"
    endpointpass="admiral"

    #Access to local dev VM
    #endpointhost="192.168.13.128"
    #endpointhost="127.0.0.1:5000"
    endpointpath="/sandbox/"
    
    # Access credentials for testing from local dev VM
    endpointuser="admin"
    endpointpass="test"

    # Later, may define methods to override these defaults, e.g. from a configuration file

# End.
