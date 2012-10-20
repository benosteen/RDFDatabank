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

from rdfdatabank.lib.doi_schema import DataciteDoiSchema
from pylons import app_globals as ag
import os, codecs, uuid

def get_doi_metadata(doi, item):
    schema = DataciteDoiSchema()
    xml_metadata = {}
    xml_metadata['identifier']= schema.xml_schema['identifier']%doi
    for key, predicates in schema.mandatory_metadata.iteritems():
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            return False
        if key == 'publicationYear':
            xml_metadata[key] = schema.xml_schema[key]%answers[0].split('-')[0]
        elif key not in schema.parent_tags:
            xml_metadata[key] = schema.xml_schema[key]%answers[0]
        else:
            xml_subset = []
            for ans in answers:
                if key == 'creator':
                    if len(ans.split(',')) == 2:
                        xml_subset.append("    "+schema.xml_schema[key]%ans)
                else:
                    xml_subset.append("    "+schema.xml_schema[key]%ans)
            if not xml_subset:
                return False
            xml_subset.insert(0, "<%s>"%schema.parent_tags[key])
            xml_subset.append("</%s>"%schema.parent_tags[key])
            xml_subset = "\n    ".join(xml_subset)
            xml_metadata[key] = xml_subset

    for grp, keys in schema.groups.iteritems():
        xml_subset = {}
        for k in keys:
            predicates = schema.optional_metadata['%s:%s'%(grp, k)]
            answers = None
            for p in predicates:
                answers = item.list_rdf_objects(item.uri, p)
                if answers:
                    break
            if not answers or not answers[0]:
                continue
            if grp =='date':
                xml_subset[k] = "    "+schema.xml_schema[k]%answers[0].split('T')[0]
            else:
                xml_subset[k] = "    "+schema.xml_schema[k]%answers[0]
        if xml_subset:
            xml_subset_str = ["<%s>"%schema.parent_tags[grp]]
            for o in schema.schema_order[grp]:
                if o in xml_subset.keys():
                    xml_subset_str.append(xml_subset[o])
            xml_subset_str.append("</%s>"%schema.parent_tags[grp])
            xml_subset_str = "\n    ".join(xml_subset_str)
            xml_metadata[grp] = xml_subset_str
    
    for key, predicates in schema.optional_metadata.iteritems():
        if ':' in key and key.split(':')[0] in schema.groups.keys():
            continue
        answers = None
        for p in predicates:
            answers = item.list_rdf_objects(item.uri, p)
            if answers:
                break
        if not answers:
            continue
        if key not in schema.parent_tags:
            xml_metadata[key] = schema.xml_schema[key]%answers[0]
        else:
            xml_subset = []
            for ans in answers:
                xml_subset.append("    "+schema.xml_schema[key]%ans)
            if xml_subset:
                xml_subset.insert(0, "<%s>"%schema.parent_tags[key])
                xml_subset.append("</%s>"%schema.parent_tags[key])
                xml_subset = "\n    ".join(xml_subset)
                xml_metadata[key] = xml_subset
    if not xml_metadata:
        return False
    fn = "/tmp/%s"%uuid.uuid4()
    f = open(fn, 'w')
    f.write("%s\n"%schema.xml_schema['header'])
    for o in schema.schema_order['all']:
        if o in xml_metadata: 
            f.write("   %s\n "%xml_metadata[o])
    f.write("%s\n"%schema.xml_schema['footer'])
    f.close()
    unicode_metadata = codecs.open(fn, 'r', encoding='utf-8').read()
    return unicode_metadata

def doi_count(increase=True):
    if not os.path.isfile(ag.doi_count_file):
        count = 0
        if increase:
            count += 1
        f = open(ag.doi_count_file, 'w')
        f.write(str(count))
        f.close()
        return count

    f = open(ag.doi_count_file, 'r')
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
    f = open(ag.doi_count_file, 'w')
    f.write(str(count))
    f.close()
    return count
