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

class DataciteDoiSchema():
    def __init__(self):
        """
            DOI service provided by the British Library on behalf of Datacite.org
            API Doc: https://api.datacite.org/
            Metadata requirements: http://datacite.org/schema/DataCite-MetadataKernel_v2.0.pdf
        """
        #Mandatory metadata
        self.mandatory_metadata={
            #'identifier':['bibo:doi'],
            'creator':['dc:creator', 'dcterms:creator'],
            'title':['dc:title', 'dcterms:title'],
            'publisher':['dc:publisher', 'dcterms:publisher'],
            'publicationYear':['oxds:embargoedUntil', 'dcterms:issued', 'dcterms:modified', 'dc:date']
        }
         
        self.optional_metadata={
            'subject':['dc:subject', 'dcterms:subject'],
            #'contributor':['dc:contributor', 'dcterms:contributor'],
            'date:accepted':['dcterms:dateAccepted'],
            'date:available':['oxds:embargoedUntil'],
            'date:copyrighted':['dcterms:dateCopyrighted'],
            'date:created':['dcterms:created'],
            'date:issued':['dcterms:issued'],
            'date:submitted':['dcterms:dateSubmitted'],
            'date:updated':['dcterms:modified'],
            #'date:valid':['dcterms:date'],
            'language':['dc:language', 'dcterms:language'],
            'resourceType':['dc:type','dcterms:type'],
            'alternateIdentifier':['dc:identifier', 'dcterms:identifier'],
            #'RelatedIdentifier':[],
            'size':['dcterms:extent'],
            'format':['dc:format', 'dcterms:format'],
            'version':['oxds:currentVersion'],
            'rights':['dc:rights', 'dcterms:rights'],
            'description:other':['dc:description', 'dcterms:description'],
            'description:abstract':['dcterms:abstract']
        }
        
        self.schema_order={
            'all':('identifier', 'creator', 'title', 'publisher', 'publicationYear', 'subject', 'contributor', 'date', 'language', 'resourceType', \
                'alternateIdentifier', 'RelatedIdentifier', 'size', 'format', 'version', 'rights', 'description'),
            'date':('accepted', 'available', 'copyrighted', 'created', 'issued', 'submitted', 'updated', 'valid'),
            'description':('other', 'abstract')
        }
        
        self.xml_schema={
            'header':"""<?xml version="1.0" encoding="utf-8"?>
<resource xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="datacite-metadata-v2.0.xsd" lastMetadataUpdate="2006-05-04" metadataVersionNumber="1">""",
            #'header':"""<resource xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="datacite-metadata-v2.0.xsd" lastMetadataUpdate="2006-05-04" metadataVersionNumber="1">""",
            #'header':"""<resource xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://datacite.org/schema/datacite-metadata-v2.0.xsd">""",
            'identifier':"""<identifier identifierType="DOI">%s</identifier>""",
            'creator':"""<creator><creatorName>%s</creatorName></creator>""",
            'title':"""<title>%s</title>""",
            'publisher':"""<publisher>%s</publisher>""",
            'publicationYear':"""<publicationYear>%s</publicationYear>""",
            'subject':"""<subject>%s</subject>""",
            'accepted':"""<date dateType="Accepted">%s</date>""",
            'available':"""<date dateType="Available">%s</date>""",
            'copyrighted':"""<date dateType="Copyrighted">%s</date>""",
            'created':"""<date dateType="Created">%s</date>""",
            'issued':"""<date dateType="Issued">%s</date>""",
            'submitted':"""<date dateType="Submitted">%s</date>""",
            'updated':"""<date dateType="Updated">%s</date>""",
            'valid':"""<date dateType="Valid">%s</date>""",
            'language':"""<language>%s</language>""",
            'resourceType':"""<resourceType resourceTypeGeneral="Dataset">%s</resourceType>""",
            'alternateIdentifier':"""<alternateIdentifier alternateIdentifierType="Publisher Identifier">%s</alternateIdentifier>""",
            'size':"""<size>%s</size>""",
            'format':"""<format>%s</format>""",
            'version':"""<version>%s</version>""",
            'rights':"""<rights>%s</rights>""",
            'other':"""<description descriptionType="Other">%s</description>""",
            'abstract':"""<description descriptionType="Abstract">%s</description>""",
            'footer':"""</resource>"""
        }

        self.parent_tags={
            'creator':'creators',
            'title':'titles',
            'subject':'subjects',
            'date':'dates',
            'alternateIdentifier':'alternateIdentifiers',
            'size':'sizes',
            'format':'formats',
            'description':'descriptions'
        }

        self.groups={
            'date':['accepted', 'available', 'copyrighted', 'created', 'issued', 'submitted', 'updated'],
            'description':['other', 'abstract']
        }
