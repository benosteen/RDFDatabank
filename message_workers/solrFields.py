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

solr_fields_mapping = {
    "silo":"silo",
    "id":"id",
    "uuid":"uuid",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":"type",
    "http://vocab.ox.ac.uk/dataset/schema#isEmbargoed":"embargoStatus",
    "http://purl.org/spar/pso/Status":"embargoStatus",
    "http://vocab.ox.ac.uk/dataset/schema#embargoedUntil":"embargoedUntilDate",
    "http://purl.org/spar/fabio/hasEmbargoDate":"embargoedUntilDate",
    "http://vocab.ox.ac.uk/dataset/schema#currentVersion":"currentVersion",
    "http://purl.org/ontology/bibo/doi":"doi",
    "http://www.openarchives.org/ore/terms/aggregates":"aggregatedResource",
    "http://purl.org/spar/fabio/publicationDate":"publicationDate",
    "http://purl.org/dc/terms/abstract":"abstract",
    "http://purl.org/dc/terms/accessRights":"accessRights",
    "http://purl.org/dc/terms/accrualMethod":"accrualMethod",
    "http://purl.org/dc/terms/accrualPeriodicity":"accrualPeriodicity",
    "http://purl.org/dc/terms/accrualPolicy":"accrualPolicy",
    "http://purl.org/dc/terms/alternative":"alternative",
    "http://purl.org/dc/terms/audience":"audience",
    "http://purl.org/dc/terms/available":"available",
    "http://purl.org/dc/terms/bibliographicCitation":"bibliographicCitation",
    "http://purl.org/dc/terms/conformsTo":"conformsTo",
    "http://purl.org/dc/terms/contributor":"contributor",
    "http://purl.org/dc/terms/coverage":"coverage",
    "http://purl.org/dc/terms/created":"created",
    "http://purl.org/dc/terms/creator":"creator",
    "http://purl.org/dc/terms/date":"date",
    "http://purl.org/dc/terms/dateAccepted":"dateAccepted",
    "http://purl.org/dc/terms/dateCopyrighted":"dateCopyrighted",
    "http://purl.org/dc/terms/dateSubmitted":"dateSubmitted",
    "http://purl.org/dc/terms/description":"description",
    "http://purl.org/dc/terms/educationLevel":"educationLevel",
    "http://purl.org/dc/terms/extent":"extent",
    "http://purl.org/dc/terms/format":"format",
    "http://purl.org/dc/terms/hasFormat":"hasFormat",
    "http://purl.org/dc/terms/hasPart":"hasPart",
    "http://purl.org/dc/terms/hasVersion":"hasVersion",
    "http://purl.org/dc/terms/identifier":"identifier",
    "http://purl.org/dc/terms/instructionalMethod":"instructionalMethod",
    "http://purl.org/dc/terms/isFormatOf":"isFormatOf",
    "http://purl.org/dc/terms/isPartOf":"isPartOf",
    "http://purl.org/dc/terms/isReferencedBy":"isReferencedBy",
    "http://purl.org/dc/terms/isReplacedBy":"isReplacedBy",
    "http://purl.org/dc/terms/isRequiredBy":"isRequiredBy",
    "http://purl.org/dc/terms/issued":"issued",
    "http://purl.org/dc/terms/isVersionOf":"isVersionOf",
    "http://purl.org/dc/terms/language":"language",
    "http://purl.org/dc/terms/license":"license",
    "http://purl.org/dc/terms/mediator":"mediator",
    "http://purl.org/dc/terms/medium":"medium",
    "http://purl.org/dc/terms/modified":"modified",
    "http://purl.org/dc/terms/provenance":"provenance",
    "http://purl.org/dc/terms/publisher":"publisher",
    "http://purl.org/dc/terms/references":"references",
    "http://purl.org/dc/terms/relation":"relation",
    "http://purl.org/dc/terms/replaces":"replaces",
    "http://purl.org/dc/terms/requires":"requires",
    "http://purl.org/dc/terms/rights":"rights",
    "http://purl.org/dc/terms/rightsHolder":"rightsHolder",
    "http://purl.org/dc/terms/source":"source",
    "http://purl.org/dc/terms/spatial":"spatial",
    "http://purl.org/dc/terms/subject":"subject",
    "http://purl.org/dc/terms/tableOfContents":"tableOfContents",
    "http://purl.org/dc/terms/temporal":"temporal",
    "http://purl.org/dc/terms/title":"title",
    "http://purl.org/dc/terms/type":"type",
    "http://purl.org/dc/terms/valid":"valid",
    "http://purl.org/dc/elements/1.1/contributor":"contributor",
    "http://purl.org/dc/elements/1.1/coverage":"coverage",         
    "http://purl.org/dc/elements/1.1/creator":"creator",
    "http://purl.org/dc/elements/1.1/date":"date",
    "http://purl.org/dc/elements/1.1/description":"description",
    "http://purl.org/dc/elements/1.1/format":"format",
    "http://purl.org/dc/elements/1.1/identifier":"identifier",
    "http://purl.org/dc/elements/1.1/language":"language",
    "http://purl.org/dc/elements/1.1/publisher":"publisher",
    "http://purl.org/dc/elements/1.1/relation":"relation",
    "http://purl.org/dc/elements/1.1/rights":"rights",
    "http://purl.org/dc/elements/1.1/source":"source",
    "http://purl.org/dc/elements/1.1/subject":"subject",
    "http://purl.org/dc/elements/1.1/title":"title",
    "http://purl.org/dc/elements/1.1/type":"type"
}

facets = [
   'f_creator', 
   'f_mediator', 
   'f_embargoedUntilDate', 
   'f_license', 
   'f_rights', 
   'f_type', 
   'f_publisher', 
   'f_isPartOf', 
   'f_hasVersion', 
   'f_publicationDate', 
   'f_contributor',
   'f_language',
   'f_rightsHolder',
   'f_source',
   'f_subject'
]
