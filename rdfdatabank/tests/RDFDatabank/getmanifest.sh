#!/bin/bash
#
# Get RDFDatabank dataset manifest using command line curl.
#

RDBROOT=http://163.1.127.173/admiral-test/datasets
DATASET=${1-test}

# --data-binary @- posts multiline from stdin

echo
echo "===== RETRIEVE DATASET $DATASET PAGE as RDF ====="
curl ${RDBROOT}/${DATASET} -u admiral:admiral -H "Accept: application/rdf+xml"

# End.
