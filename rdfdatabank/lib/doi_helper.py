from rdfdatabank.config.doi_config import OxDataciteDoi

get_doi_metadata(item):
    xml_metadata = OxDataciteDoi.xml_schema['header']
    for key, predicates OxDataciteDoi.mandatory_metadata.iteritems():
        ans = None
        for p in predicates:
            ans = item.list_rdf_objects(item.uri, p)
            
            
        