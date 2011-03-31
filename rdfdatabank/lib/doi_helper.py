from rdfdatabank.config.doi_config import OxDataciteDoi
import os

def get_doi_metadata(item):
    doi_conf = OxDataciteDoi()
    xml_metadata = []
    for key, predicates in doi_conf.mandatory_metadata.iteritems():
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            return False
        if key == 'publicationYear':
            xml_metadata.append(doi_conf.xml_schema[key]%answers[0].split('-')[0])
        elif key not in doi_conf.parent_tags:
            xml_metadata.append(doi_conf.xml_schema[key]%answers[0])
        else:
            xml_subset = []
            for ans in answers:
                if key == 'creator':
                    if len(ans.split(',')) == 2:
                        xml_subset.append("    "+doi_conf.xml_schema[key]%ans)
                else:
                    xml_subset.append("    "+doi_conf.xml_schema[key]%ans)
            if not xml_subset:
                return False
            xml_subset.insert(0, "<%s>"%doi_conf.parent_tags[key])
            xml_subset.append("</%s>"%doi_conf.parent_tags[key])
            xml_subset = "\n    ".join(xml_subset)
            xml_metadata.append(xml_subset)            

    for grp, keys in doi_conf.groups.iteritems():
        for k in keys:    
            predicates = doi_conf.optional_metadata['%s:%s'%(grp, k)]
            xml_subset = []
            answers = None
            for p in predicates:
                answers = item.list_rdf_objects(item.uri, p)
                if answers:
                    break
            if not answers:
                continue
            xml_subset.append("    "+doi_conf.xml_schema[k]%answers[0])
        if xml_subset:
            xml_subset.insert(0, "<%s>"%doi_conf.parent_tags[grp])
            xml_subset.append("</%s>"%doi_conf.parent_tags[grp])
            xml_subset = "\n    ".join(xml_subset)
            xml_metadata.append(xml_subset)
    
    for key, predicates in doi_conf.optional_metadata.iteritems():
        if ':' in key and key.split(':')[0] in doi_conf.groups.keys():
            continue
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            continue
        if key not in doi_conf.parent_tags:
            #f = open('/opt/rdfdatabank/src/logs/doi_debug.log', 'a')
            #f.write(str(doi_conf.xml_schema[key]) + '\n')
            #f.write(str(answers[0]) + '\n')
            #f.close()
            xml_metadata.append(doi_conf.xml_schema[key]%answers[0])
        else:
            xml_subset = []
            for ans in answers:
                xml_subset.append("    "+doi_conf.xml_schema[key]%ans)
            if xml_subset:
                xml_subset.insert(0, "<%s>"%doi_conf.parent_tags[key])
                xml_subset.append("</%s>"%doi_conf.parent_tags[key])
                xml_subset = "\n    ".join(xml_subset)
                xml_metadata.append(xml_subset)
    if not xml_metadata:
        return False
    xml_metadata.insert(0, doi_conf.xml_schema['header'])
    xml_metadata = "\n    ".join(xml_metadata)
    xml_metadata = xml_metadata + "\n%s"%doi_conf.xml_schema['footer']
    return xml_metadata

def doi_count(increase=True):
    doi_conf = OxDataciteDoi()
    if not os.path.isfile(doi_conf.doi_count_file):
        count = 0
        if increase:
            count += 1
        f = open(doi_conf.doi_count_file, 'w')
        f.write(str(count))
        f.close()
        return count

    f = open(doi_conf.doi_count_file, 'r')
    count = f.read()
    f.close()
    try:
        count = int(count)
    except:
        return False
    if increase:
        count += 1
        f = open(doi_conf.doi_count_file, 'w')
        f.write(str(count))
        f.close()
    return count
