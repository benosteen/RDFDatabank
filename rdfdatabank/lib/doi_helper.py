from rdfdatabank.config.doi_config import OxDataciteDoi
import os, codecs, uuid

def get_doi_metadata(doi, item):
    doi_conf = OxDataciteDoi()
    xml_metadata = {}
    xml_metadata['identifier']= doi_conf.xml_schema['identifier']%doi
    for key, predicates in doi_conf.mandatory_metadata.iteritems():
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            return False
        if key == 'publicationYear':
            xml_metadata[key] = doi_conf.xml_schema[key]%answers[0].split('-')[0]
        elif key not in doi_conf.parent_tags:
            xml_metadata[key] = doi_conf.xml_schema[key]%answers[0]
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
            xml_metadata[key] = xml_subset

    for grp, keys in doi_conf.groups.iteritems():
        xml_subset = {}
        for k in keys:
            predicates = doi_conf.optional_metadata['%s:%s'%(grp, k)]
            answers = None
            for p in predicates:
                answers = item.list_rdf_objects(item.uri, p)
                if answers:
                    break
            if not answers or not answers[0]:
                continue
            if grp =='date':
                xml_subset[k] = "    "+doi_conf.xml_schema[k]%answers[0].split('T')[0]
            else:
                xml_subset[k] = "    "+doi_conf.xml_schema[k]%answers[0]
        if xml_subset:
            xml_subset_str = ["<%s>"%doi_conf.parent_tags[grp]]
            for o in doi_conf.schema_order[grp]:
                if o in xml_subset.keys():
                    xml_subset_str.append(xml_subset[o])
            xml_subset_str.append("</%s>"%doi_conf.parent_tags[grp])
            xml_subset_str = "\n    ".join(xml_subset_str)
            xml_metadata[grp] = xml_subset_str
    
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
            xml_metadata[key] = doi_conf.xml_schema[key]%answers[0]
        else:
            xml_subset = []
            for ans in answers:
                xml_subset.append("    "+doi_conf.xml_schema[key]%ans)
            if xml_subset:
                xml_subset.insert(0, "<%s>"%doi_conf.parent_tags[key])
                xml_subset.append("</%s>"%doi_conf.parent_tags[key])
                xml_subset = "\n    ".join(xml_subset)
                xml_metadata[key] = xml_subset
    if not xml_metadata:
        return False
    fn = "/tmp/%s"%uuid.uuid4()
    f = open(fn, 'w')
    f.write("%s\n"%doi_conf.xml_schema['header'])
    for o in doi_conf.schema_order['all']:
        if o in xml_metadata: 
            f.write("   %s\n "%xml_metadata[o])
    f.write("%s\n"%doi_conf.xml_schema['footer'])
    f.close()
    unicode_metadata = codecs.open(fn, 'r', encoding='utf-8').read()
    return unicode_metadata

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
    count = count.replace('\n', '').strip()
    try:
        count = int(count)
    except:
        return False
    if not increase:
        return str(count)

    count += 1
    f = open(doi_conf.doi_count_file, 'w')
    f.write(str(count))
    f.close()
    return count
