import subprocess

import os

from redis import Redis

from uuid import uuid4

from rdfdatabank.lib.utils import create_new

#import checkm

zipfile_root = "zipfile:"

class BadZipfile(Exception):
    """Cannot open zipfile using commandline tool 'unzip' to target directory"""

def get_next_zipfile_id(siloname):
    # TODO make this configurable
    r = Redis()
    return str(r.incr("%s:zipfile" % (siloname)))

def find_last_zipfile(silo):
    siloname = silo.state['storage_dir']
    r = Redis()
    r.set("%s:zipfile" % (siloname), 0)
    zipfile_id = 0
    while(silo.exists("%s%s" % (zipfile_root, zipfile_id))):
        zipfile_id = r.incr("%s:zipfile" % (siloname))
    return zipfile_id

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
    # TODO add the checkm stuff back in
    if not target_directory:
        target_directory = "/tmp/%s" % (uuid4().hex)
    p = subprocess.Popen("unzip -d %s %s" % (target_directory, filepath), shell=True, stdout=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        raise BadZipfile
    else:
        return target_directory
     
def unpack_zip_item(zip_item, silo, ident):
    derivative = zip_item.list_rdf_objects("*", "dcterms:hasVersion")
    # 1 object holds 1 zipfile - may relax this easily given demand
    assert len(derivative.keys()) == 1
    for file_uri in derivative.keys():
        filepath = file_uri[len(zip_item.uri)+1:]
        real_filepath = zip_item.to_dirpath(filepath)
        target_item = derivative[file_uri][0][len(silo.state['uri_base']):]
        
        # Overwrite current version instead of making new version?
        
        to_item = create_new(silo, target_item, ident)
        #to_item = silo.get_item(target_item)
        unpacked_dir = unzip_file(real_filepath)
        to_item.move_directory_as_new_version(unpacked_dir)
        to_item.add_triple(to_item.uri, "dcterms:isVersionOf", file_uri)
        to_item.sync()
        return True
            
