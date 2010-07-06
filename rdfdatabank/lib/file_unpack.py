import subprocess

from datetime import datetime

import os

from redis import Redis

from uuid import uuid4

from rdfdatabank.lib.utils import create_new

#import checkm

zipfile_root = "zipfile:"

class BadZipfile(Exception):
    """Cannot open zipfile using commandline tool 'unzip' to target directory"""
    
def check_file_mimetype(real_filepath, mimetype):
    p = subprocess.Popen("file -ib %s" %(real_filepath), shell=True, stdout=subprocess.PIPE)
    output_file = p.stdout
    output_str = output_file.read()
    if mimetype in output_str:
        return True
    else:
        return False
        
def get_zipfiles_in_dataset(dataset):
    derivative = dataset.list_rdf_objects("*", "ore:aggregates")
    #print "derivative ", derivative
    #print "derivative values", derivative.values()[0]
    zipfiles = {}
    if derivative and derivative.values() and derivative.values()[0]:
        for file_uri in derivative.values()[0]:
            filepath = file_uri[len(dataset.uri)+1:]
            real_filepath = dataset.to_dirpath(filepath)
            #print "file_uri : ", file_uri
            #print "filepath : ", filepath
            #print "real_filepath : ", real_filepath
            if check_file_mimetype(real_filepath, 'application/zip'): 
                (fn, ext) = os.path.splitext(filepath)
                zipfiles[filepath]="%s-%s"%(dataset.item_id, fn)
    return zipfiles
        
def store_zipfile(silo, target_item_uri, POSTED_file, ident):
    zipfile_id = get_next_zipfile_id(silo.state['storage_dir'])
    while(silo.exists("%s%s" % (zipfile_root, zipfile_id))):
        zipfile_id = get_next_zipfile_id(silo.state['storage_dir'])
    
    #zip_item = silo.get_item("%s%s" % (zipfile_root, zipfile_id))
    zip_item = create_new(silo, "%s%s" % (zipfile_root, zipfile_id), ident)
    zip_item.add_triple("%s/%s" % (zip_item.uri, POSTED_file.filename.lstrip(os.sep)), "dcterms:hasVersion", target_item_uri)
    zip_item.put_stream(POSTED_file.filename, POSTED_file.file)
    try:
        POSTED_file.file.close()
    except:
        pass
    zip_item.sync()
    return zip_item

def unzip_file(filepath, target_directory=None):
    f = open("/tmp/python_out.log", "a")
    f.write("\n--------------- In unzip file -------------------\n")
    f.write("filepath : %s\n"%str(filepath))
    f.write('-'*40+'\n')
    f.close()
    # TODO add the checkm stuff back in
    if not target_directory:
        target_directory = "/tmp/%s" % (uuid4().hex)
    p = subprocess.Popen("unzip -d %s %s" % (target_directory, filepath), shell=True, stdout=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        raise BadZipfile
    else:
        return target_directory
     
def get_items_in_dir(items_list, dirname, fnames):
    for fname in fnames:
        items_list.append(os.path.join(dirname,fname))
    return

def unpack_zip_item(target_dataset_name, current_dataset, zip_item, silo, ident):
    f = open("/tmp/python_out.log", "a")
    f.write("\n--------------- In unpack zip item -------------------\n")
    f.write("target item :%s\n"%str(target_dataset_name))
    f.write("zip item: %s \n"%str(zip_item))
    filepath = current_dataset.to_dirpath(zip_item)    
    f.write("filepath : %s\n"%filepath)
    f.write('-'*40+'\n')
    f.close()
    unpacked_dir = unzip_file(filepath)
    target_dataset = create_new(silo, target_dataset_name, ident)
    
    file_uri = current_dataset.uri
    if not file_uri.endswith('/'):
        file_uri += '/'
    file_uri = "%s%s"%(file_uri,zip_item)
                
    items_list = []
    os.path.walk(unpacked_dir,get_items_in_dir,items_list)
    target_dataset.move_directory_as_new_version(unpacked_dir)
    target_dataset.add_namespace('oxds', "http://vocab.ox.ac.uk/dataset/schema#")
    unp_dir = unpacked_dir
    if not unp_dir.endswith('/'):
        unp_dir += '/'
    target_uri_base = target_dataset.uri
    if not target_uri_base.endswith('/'):
        target_uri_base += '/'
    for i in items_list:
        i = i.replace(unp_dir, '')
        target_dataset.add_triple(target_dataset.uri, "ore:aggregates", "%s%s"%(target_uri_base,i))
    target_dataset.add_triple(target_dataset.uri, "rdf:type", "oxds:Grouping")
    target_dataset.add_triple(target_dataset.uri, u"dcterms:modified", datetime.now())
    target_dataset.add_triple(target_dataset.uri, "dcterms:isVersionOf", file_uri)
    target_dataset.sync()
    current_dataset.add_triple("%s/%s" % (current_dataset.uri, zip_item.lstrip(os.sep)), "dcterms:hasVersion", target_dataset.uri)
    current_dataset.sync()
    return True
