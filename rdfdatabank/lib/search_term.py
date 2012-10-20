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


class term_list():
    def get_all_search_fields(self):
        return [
        "silo",
        "id",
        "uuid",
        "embargoStatus",
        "embargoedUntilDate",
        "currentVersion",
        "doi",
        "aggregatedResource",
        "publicationDate",
        "abstract",
        "accessRights",
        "accrualMethod",
        "accrualPeriodicity",
        "accrualPolicy",
        "alternative",
        "audience",
        "available",
        "bibliographicCitation",
        "conformsTo",
        "contributor",
        "coverage",
        "created",
        "creator",
        "date",
        "dateAccepted",
        "dateCopyrighted",
        "dateSubmitted",
        "description",
        "educationLevel",
        "extent",
        "format",
        "hasFormat",
        "hasPart",
        "hasVersion",
        "identifier",
        "instructionalMethod",
        "isFormatOf",
        "isPartOf",
        "isReferencedBy",
        "isReplacedBy",
        "isRequiredBy",
        "issued",
        "isVersionOf",
        "language",
        "license",
        "mediator",
        "medium",
        "modified",
        "provenance",
        "publisher",
        "references",
        "relation",
        "replaces",
        "requires",
        "rights",
        "rightsHolder",
        "source",
        "spatial",
        "subject",
        "tableOfContents",
        "temporal",
        "title",
        "type",
        "valid",
        "f_creator",
        "f_mediator",
        "f_embargoedUntilDate",
        "f_license",
        "f_rights",
        "f_type",
        "f_publisher",
        "f_isPartOf",
        "f_hasVersion",
        "f_publicationDate",
        "f_contributor",
        "f_language",
        "f_rightsHolder",
        "f_source",
        "f_subject",
        "timestamp"
        ]

    def get_search_field_dictionary(self):
        field_names = {
        "silo":"Silo",
        "id":"Identifier",
        "uuid":"Unique Identifier",
        "embargoStatus":"Embargo status",
        "embargoedUntilDate":"Embargoed until date",
        "currentVersion":"Current version",
        "doi":"DOI",
        "aggregatedResource":"Aggregated resource",
        "publicationDate":"Publication date",
        "abstract":"Abstract",
        "accessRights":"Access rights",
        "accrualMethod":"Accrual method",
        "accrualPeriodicity":"Accrual periodicity",
        "accrualPolicy":"Accrual policy",
        "alternative":"Alternative title",
        "audience":"Audience",
        "available":"Availability",
        "bibliographicCitation":"Bibliographic citation",
        "conformsTo":"Conforms to",
        "contributor":"Contributor",
        "coverage":"Coverage",
        "created":"Date created",
        "creator":"Creator",
        "date":"Date",
        "dateAccepted":"Date accepted",
        "dateCopyrighted":"Date copyrighted",
        "dateSubmitted":"Date submitted",
        "description":"Description",
        "educationLevel":"Education level",
        "extent":"Extent",
        "format":"Format",
        "hasFormat":"Has format",
        "hasPart":"Has part",
        "hasVersion":"Has version",
        "identifier":"Identifier",
        "instructionalMethod":"Instructional method",
        "isFormatOf":"Is format of",
        "isPartOf":"Is part of",
        "isReferencedBy":"Is referenced by",
        "isReplacedBy":"Is replaced by",
        "isRequiredBy":"Is required by",
        "issued":"Date issued",
        "isVersionOf":"Is version Of",
        "language":"Language",
        "license":"License",
        "mediator":"Mediator",
        "medium":"Medium",
        "modified":"Date modified",
        "provenance":"Provenance",
        "publisher":"Publisher",
        "references":"References",
        "relation":"Relation",
        "replaces":"Replaces",
        "requires":"Requires",
        "rights":"Rights",
        "rightsHolder":"Rights holder",
        "source":"Source",
        "spatial":"Spatial coverage",
        "subject":"Subject",
        "tableOfContents":"Table of contents",
        "temporal":"Temporal coverage",
        "title":"Title",
        "type":"Type",
        "valid":"Valid",
        "f_creator":"Creator",
        "f_mediator":"Mediator",
        "f_embargoedUntilDate":"Embargoed until date",
        "f_license":"License",
        "f_rights":"Rights",
        "f_type":"Type",
        "f_publisher":"Publisher",
        "f_isPartOf":"Is part of",
        "f_hasVersion":"Has version",
        "f_publicationDate":"Publication date",
        "f_contributor":"Contributor",
        "f_language":"Language",
        "f_rightsHolder":"Rights holder",
        "f_source":"Source",
        "f_subject":"Subject",
        "timestamp":"Information indexed on"
        }
        return field_names
        
    def get_type_field_dictionary(self):
        type_names = {
        "silo":'Silos',
        "dataset":"Data packages",
        "item":"File names",
        "all":"Any level"
        }
        return type_names

    def get_all_facet_fields(self):
        return [
        "silo",
        "embargoStatus",
        "f_creator",
        "f_mediator",
        "f_embargoedUntilDate",
        "f_license",
        "f_rights",
        "f_type",
        "f_publisher",
        "f_isPartOf",
        "f_hasVersion",
        "f_publicationDate",
        "f_contributor",
        "f_language",
        "f_rightsHolder",
        "f_source",
        "f_subject"
        ]

    def get_range_facet_fields(self):
        return [
        "f_embargoedUntilDate",
        "f_publicationDate"
        ]
