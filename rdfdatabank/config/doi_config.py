class OxDataciteDoi():
    def __init__(self):
        """
            DOI service provided by the British Library on behalf of Datacite.org
            API Doc: https://api.datacite.org/
            Metadata requirements: http://datacite.org/schema/DataCite-MetadataKernel_v2.0.pdf
        """
        #Details pertaining to Oxford account with datacite
        self.account = "BL.OXDB"
        self.description = "Oxford University Library Service Databank"
        self.contact = "Anusha Ranganathan"
        self.email = "Anusha.Ranganathan@bodleian.ox.ac.uk"
        self.password = "oxdvksf432wer987"
        self.domain = "ox.ac.uk"
        self.prefix = "10.5287"
        self.quota = 500
        self.doi_count_file = "/opt/rdfdatabank/src/rdfdatabank/config/doi_count"
        f = open(self.doi_count_file, 'w')
        f.write('0')
        f.close()
        
        #Datacite api endpoint
        self.endpoint_host = "https://api.datacite.org"
        self.endpoint_path_doi = "/doi"
        self.endpoint_path_metadata = "/metadata"
        
        #Mandatory metadata
        self.mandatory_metadata={
            'identifier':['bibo:doi'],
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
            'date:updated':['dcterms:modified']
            #'date:Valid':['dcterms:date']
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
        
        self.xml_schema={
            'header':"""<resource xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:noNamespaceSchemaLocation="datacite-metadata-v2.0.xsd" lastMetadataUpdate="2006-05-04" metadataVersionNumber="1">""",
            'identifier':"""<identifier identifierType="DOI">%s</identifier>""",
            'creator':"""<creatorName>%s</creatorName>""",
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
            'language':"""<language>%s</language>""",
            'resourceType':"""<resourceType resourceTypeGeneral="Dataset">%s</resourceType>""",
            'alternateIdentifier':"""<alternateIdentifier alternateIdentifierType="Publisher Identifier">%s</alternateIdentifier>""",
            'size':"""<size>%s</size>""",
            'format':"""<format>%s</format>""",
            'version':"""<version>1.0</version>""",
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
