from rdfdatabank.config.doi_config import OxDataciteDoi

get_doi_metadata(item):
    xml_metadata = OxDataciteDoi.xml_schema['header']
    for key, predicates in OxDataciteDoi.mandatory_metadata.iteritems():
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            return False
        if key == 'publicationYear':
            xml_metadata.append("    "+OxDataciteDoi.xml_schema[key]%answers[0].split('-')[0])
        elif key not in self.parent_tags:
            xml_metadata.append("    "+OxDataciteDoi.xml_schema[key]%answers[0])
        else:
            xml_subset = []
            for ans in answers:
                if key == 'creator':
                    if len(ans_split(',')) == 2:
                        xml_subset.append("    "+OxDataciteDoi.xml_schema[key]%ans)
                else:
                    xml_subset.append("    "+OxDataciteDoi.xml_schema[key]%ans)
            if not xml_subset:
                return False
            xml_subset.insert(0, "<%s>"%OxDataciteDoi.parent_tags[key])
            xml_subset.append("</%s>"%OxDataciteDoi.parent_tags[key])
            xml_subset = "\n    ".join(xml_subset)
            xml_metadata.append(xml_subset)            

    for grp, keys in OxDataciteDoi.groups.iteritems():
        for k in keys:    
            predicates = OxDataciteDoi.optional_metadata['%s:%s'%(grp, k)
            xml_subset = []
            answers = None
            for p in predicates:
                answers = item.list_rdf_objects(item.uri, p)
                if answers:
                    break
            if not answers:
                continue
            xml_subset.append("    "+OxDataciteDoi.xml_schema[k]%answers[0])
        if xml_subset:
            xml_subset.insert(0, "<%s>"%OxDataciteDoi.parent_tags[grp])
            xml_subset.append("</%s>"%OxDataciteDoi.parent_tags[grp])
            xml_subset = "\n    ".join(xml_subset)
            xml_metadata.append(xml_subset)
    
    for key, predicates in OxDataciteDoi.optional_metadata.iteritems():
        if ':' in key and key.split(':')[0] in OxDataciteDoi.groups.keys():
            continue
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            continue
        if key not in self.parent_tags:
            xml_metadata.append("    "+OxDataciteDoi.xml_schema[key]%answers[0])
        else:
            xml_subset = []
            for ans in answers:
                xml_subset.append("    "+OxDataciteDoi.xml_schema[key]%ans)
            if xml_subset:
                xml_subset.insert(0, "<%s>"%OxDataciteDoi.parent_tags[key])
                xml_subset.append("</%s>"%OxDataciteDoi.parent_tags[key])
                xml_subset = "\n    ".join(xml_subset)
                xml_metadata.append(xml_subset)
    if not xml_metadata:
        return False
    xml_metadata.insert(0, OxDataciteDoi.xml_schema['header'])
    xml_metadata = "\n    ".join(xml_metadata)
    xml_metadata = xml_metadata + "\n%s"%OxDataciteDoi.xml_schema['footer']
    return xml_metadata

doi_count(increase=True):
    if not os.path.isfile(OxDataciteDoi.doi_count_file):
        count = 0
        if increase:
            count += 1
        f = open(OxDataciteDoi.doi_count_file, 'w')
        f.write(str(count))
        f.close()
        return count

    f = open(OxDataciteDoi.doi_count_file, 'r')
    count = f.read()
    f.close()
    try:
        count = int(count)
    except:
        count = 0
    if increase:
        count += 1
        f = open(OxDataciteDoi.doi_count_file, 'w')
        f.write(str(count))
        f.close()
    return count
