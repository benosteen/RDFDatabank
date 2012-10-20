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

import subprocess
from threading import Thread
from datetime import datetime, timedelta
import os, shutil
from uuid import uuid4
from rdflib import URIRef, Literal
from rdfdatabank.lib.utils import create_new, munge_manifest, test_rdf

from pylons import app_globals as ag

#import checkm
from zipfile import ZipFile, BadZipfile as BZ

zipfile_root = "zipfile:"

class BadZipfile(Exception):
    """Cannot open zipfile using commandline tool 'unzip' to target directory"""
   
def check_file_mimetype(real_filepath, mimetype):
    if os.path.isdir(real_filepath):
        return False
    if os.path.islink(real_filepath):
        real_filepath = os.readlink(real_filepath)
    if not os.path.isfile(real_filepath):
        return False
    p = subprocess.Popen("file -ib '%s'" %(real_filepath), shell=True, stdout=subprocess.PIPE)
    output_file = p.stdout
    output_str = output_file.read()
    if mimetype in output_str:
        return True
    else:
        return False
        
def get_zipfiles_in_dataset(dataset):
    derivative = dataset.list_rdf_objects("*", "ore:aggregates")
    zipfiles = {}
    #if derivative and derivative.values() and derivative.values()[0]:
    if derivative:
        #for file_uri in derivative.values()[0]:
        for file_uri in derivative:
            if not file_uri.lower().endswith('.zip'):
                continue
            filepath = file_uri[len(dataset.uri)+1:]
            real_filepath = dataset.to_dirpath(filepath)
            if os.path.islink(real_filepath):
                real_filepath = os.readlink(real_filepath)
            if check_file_mimetype(real_filepath, 'application/zip'): 
                (fn, ext) = os.path.splitext(filepath)
                #zipfiles[filepath]="%s-%s"%(dataset.item_id, fn)
                zipfiles[filepath]=dataset.item_id
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

def read_zipfile(filepath):
    try:
        tmpfile = ZipFile(filepath, "r")
    except BZ:
        raise BadZipfile

    # list filenames
    #list_of_files = tmpfile.namelist()
    
    # file information
    zipfile_contents = {}
    for info in tmpfile.infolist():
        zipfile_contents[info.filename] = (info.file_size, info.date_time)
    tmpfile.close()
    return zipfile_contents

def read_file_in_zipfile(filepath, filename):
    try:
        tmpfile = ZipFile(filepath, "r")
    except BZ:
        raise BadZipfile

    try:
        fileinfo = tmpfile.getinfo(filename)
    except KeyError:
        return False
    if fileinfo.file_size == 0:
        return 0

    # read file
    file_contents = None
    file_contents = tmpfile.read(filename)
    tmpfile.close()
    return file_contents

def get_file_in_zipfile(filepath, filename, targetdir):
    try:
        tmpfile = ZipFile(filepath, "r")
    except BZ:
        raise BadZipfile

    try:
        fileinfo = tmpfile.getinfo(filename)
    except KeyError:
        return False
    if fileinfo.file_size == 0:
        return 0

    # extract file
    targetfile = tmpfile.extract(filename, targetdir)
    tmpfile.close()
    return targetfile

def unzip_file(filepath, target_directory=None):
    # TODO add the checkm stuff back in
    if not target_directory:
        target_directory = "/tmp/%s" % (uuid4().hex)
    p = subprocess.Popen("unzip -qq -d %s %s" % (target_directory, filepath), shell=True, stdout=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        raise BadZipfile
    else:
        return target_directory
     
def get_items_in_dir(items_list, dirname, fnames):
    for fname in fnames:
        items_list.append(os.path.join(dirname,fname))
    return

def unpack_zip_item(target_dataset, current_dataset, zip_item, silo, ident):
    filepath = current_dataset.to_dirpath(zip_item)
    if os.path.islink(filepath):
        filepath = os.readlink(filepath)
    emb = target_dataset.metadata.get('embargoed')
    emb_until = target_dataset.metadata.get('embargoed_until')

    # -- Step 1 -----------------------------
    unpacked_dir = unzip_file(filepath)

    # -- Step 2 -----------------------------
    file_uri = current_dataset.uri
    if not file_uri.endswith('/'):
        file_uri += '/'
    file_uri = "%s%s?version=%s"%(file_uri,zip_item,current_dataset.currentversion)
     
    items_list = []
    os.path.walk(unpacked_dir,get_items_in_dir,items_list)

    # -- Step 3 -----------------------------
    mani_file = None
    #Read manifest    
    for i in items_list:
        if 'manifest.rdf' in i and os.path.isfile(i):
            mani_file = os.path.join('/tmp', uuid4().hex)
            shutil.move(i, mani_file)
            items_list.remove(i)
            #os.remove(i)
            break

    # -- Step 4 -----------------------------
    #Copy unpacked dir as new version
    target_dataset.move_directory_as_new_version(unpacked_dir, log="Unpacked file %s. Contents"%zip_item)

    # -- Step 5 -----------------------------
    #Add type and isVersionOf metadata
    target_dataset.add_namespace('oxds', "http://vocab.ox.ac.uk/dataset/schema#")
    target_dataset.add_triple(target_dataset.uri, u"rdf:type", "oxds:Grouping")
    target_dataset.add_triple(target_dataset.uri, "dcterms:isVersionOf", file_uri)
    #TODO: Adding the following metadata again as moving directory deletes all this information. Need to find a better way
    if emb:
        target_dataset.add_triple(target_dataset.uri, u"oxds:isEmbargoed", 'True')
        if emb_until:
            target_dataset.add_triple(target_dataset.uri, u"oxds:embargoedUntil", emb_until)
    else:
        target_dataset.add_triple(target_dataset.uri, u"oxds:isEmbargoed", 'False')
    #The embargo
    #embargoed_until_date = (datetime.now() + timedelta(days=365*70)).isoformat()
    #target_dataset.add_triple(target_dataset.uri, u"oxds:embargoedUntil", embargoed_until_date)
    target_dataset.add_triple(target_dataset.uri, u"dcterms:identifier", target_dataset.item_id)
    target_dataset.add_triple(target_dataset.uri, u"dcterms:mediator", ident)
    target_dataset.add_triple(target_dataset.uri, u"dcterms:publisher", ag.publisher)
    if ag.rights and ag.rights.startswith('http'):
        target_dataset.add_triple(target_dataset.uri, u"dcterms:rights", URIRef(ag.rights))
    elif ag.rights:
        target_dataset.add_triple(target_dataset.uri, u"dcterms:rights", Literal(ag.rights))
    if ag.license and ag.license.startswith('http'):
        target_dataset.add_triple(target_dataset.uri, u"dcterms:license", URIRef(ag.license))
    elif ag.license:
        target_dataset.add_triple(target_dataset.uri, u"dcterms:license", Literal(ag.license))
    target_dataset.add_triple(target_dataset.uri, u"dcterms:created", datetime.now())
    target_dataset.add_triple(target_dataset.uri, u"oxds:currentVersion", target_dataset.currentversion)
    #Adding ore aggregates
    unp_dir = unpacked_dir
    if not unp_dir.endswith('/'):
        unp_dir += '/'
    target_uri_base = target_dataset.uri
    if not target_uri_base.endswith('/'):
        target_uri_base += '/'
    for i in items_list:
        i = i.replace(unp_dir, '')
        target_dataset.add_triple(target_dataset.uri, "ore:aggregates", "%s%s"%(target_uri_base,i))
    target_dataset.add_triple(target_dataset.uri, u"dcterms:modified", datetime.now())
    target_dataset.sync()

    # -- Step 6 -----------------------------
    #Munge rdf
    #TODO: If manifest is not well formed rdf - inform user. Currently just ignored.
    if mani_file and os.path.isfile(mani_file) and test_rdf(mani_file):
        munge_manifest(mani_file, target_dataset)
        os.remove(mani_file)
        
    # -- Step 7 -----------------------------
    #uri_s = "%s/%s" % (current_dataset.uri, zip_item.lstrip(os.sep))
    #uri_p = "%s?version=%s" % (target_dataset.uri, target_dataset.currentversion)
    #current_dataset.add_triple(uri_s, "dcterms:hasVersion", uri_p)
    #current_dataset.sync()

    target_dataset.sync()
    target_dataset.sync()
    target_dataset.sync()
    return True

"""
class unpack_zip_item(Thread):
    def __init__ (self, target_dataset, current_dataset, zip_item, silo, ident):
        Thread.__init__(self)
        self.target_dataset = target_dataset
        self.current_dataset = current_dataset
        self.zip_item = zip_item
        self.silo =silo
        self.ident = ident

    def run(self):
        filepath = self.current_dataset.to_dirpath(self.zip_item)
        if os.path.islink(filepath):
            filepath = os.readlink(filepath)

        # -- Step 1 -----------------------------
        unpacked_dir = unzip_file(filepath)

        # -- Step 2 -----------------------------
        file_uri = self.current_dataset.uri
        if not file_uri.endswith('/'):
            file_uri += '/'
        file_uri = "%s%s"%(file_uri,self.zip_item)
     
        items_list = []
        os.path.walk(unpacked_dir,get_items_in_dir,items_list)

        # -- Step 3 -----------------------------
        mani_file = None
        #Read manifest    
        for i in items_list:
            if 'manifest.rdf' in i and os.path.isfile(i):
                mani_file = os.path.join('/tmp', uuid4().hex)
                shutil.move(i, mani_file)
                items_list.remove(i)
                #os.remove(i)
                break
    
        # -- Step 4 -----------------------------
        #Copy unpacked dir as new version
        self.target_dataset.move_directory_as_new_version(unpacked_dir)
    
        # -- Step 5 -----------------------------
        #Add type and isVersionOf metadata
        self.target_dataset.add_namespace('oxds', "http://vocab.ox.ac.uk/dataset/schema#")
        self.target_dataset.add_triple(self.target_dataset.uri, u"rdf:type", "oxds:Grouping")
        self.target_dataset.add_triple(self.target_dataset.uri, "dcterms:isVersionOf", file_uri)
        #TODO: Adding the following metadata again as moving directory deletes all this information. Need to find a better way
        embargoed_until_date = (datetime.now() + timedelta(days=365*70)).isoformat()
        self.target_dataset.add_triple(self.target_dataset.uri, u"oxds:isEmbargoed", 'True')
        self.target_dataset.add_triple(self.target_dataset.uri, u"oxds:embargoedUntil", embargoed_until_date)
        self.target_dataset.add_triple(self.target_dataset.uri, u"dcterms:identifier", self.target_dataset.item_id)
        self.target_dataset.add_triple(self.target_dataset.uri, u"dcterms:mediator", self.ident)
        self.target_dataset.add_triple(self.target_dataset.uri, u"dcterms:publisher", ag.publisher)
        self.target_dataset.add_triple(self.target_dataset.uri, u"dcterms:created", datetime.now())
        self.target_dataset.add_triple(self.target_dataset.uri, u"oxds:currentVersion", self.target_dataset.currentversion)
        #Adding ore aggregates
        unp_dir = unpacked_dir
        if not unp_dir.endswith('/'):
            unp_dir += '/'
        target_uri_base = self.target_dataset.uri
        if not target_uri_base.endswith('/'):
            target_uri_base += '/'
        for i in items_list:
            i = i.replace(unp_dir, '')
            self.target_dataset.add_triple(self.target_dataset.uri, "ore:aggregates", "%s%s"%(target_uri_base,i))
        self.target_dataset.add_triple(self.target_dataset.uri, u"dcterms:modified", datetime.now())
        self.target_dataset.sync()
    
        # -- Step 6 -----------------------------
        #Munge rdf
        #TODO: If manifest is not well formed rdf - inform user. Currently just ignored.
        if mani_file and os.path.isfile(mani_file) and test_rdf(mani_file):
            munge_manifest(mani_file, self.target_dataset, manifest_type='http://vocab.ox.ac.uk/dataset/schema#Grouping')
         
        # -- Step 7 -----------------------------
        #Delete the status 
        self.target_dataset.del_triple(self.target_dataset.uri, u"dcterms:status")
        self.target_dataset.sync()
        self.target_dataset.sync()
        self.target_dataset.sync()
        self.current_dataset.add_triple("%s/%s" % (self.current_dataset.uri, self.zip_item.lstrip(os.sep)), "dcterms:hasVersion", self.target_dataset.uri)
        self.current_dataset.sync()
"""
