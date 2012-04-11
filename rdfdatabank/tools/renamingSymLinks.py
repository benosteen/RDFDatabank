#-*- coding: utf-8 -*-
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

"""
This program is used to rename symlinks when the location of silos has changed
1. Move silo from your old location to the new location
2. Run this script using 

$python renamingSymLinks.py OLDPATH NEWPATH

   OR by calling the function rewrite_links

OLDPATH = "/opt/RDFDatabank/silos"
NEWPATH = "/silos"

src_dirs = [
   '/silos/dataflow/pairtree_root'
  ,'/silos/demo/pairtree_root'
  ,'/silos/test/pairtree_root'
]

for src_dir in src_dirs:
  print "starting", src_dir
  rewrite_links(src_dir, OLDPATH, NEWPATH)
"""

import os
import sys

def get_links_in_dir(items_list, dirname, fnames):
    for fname in fnames:
        a = os.path.join(dirname,fname)
        #if fname == 'obj':
        #    print a            
        if os.path.islink(a):
            items_list.append(os.path.join(dirname,fname))
    return
    
def rewrite_links(src_dir, OLDPATH, NEWPATH):
    links_list = []
    os.path.walk(src_dir,get_links_in_dir,links_list)
    
    for i in range(len(links_list)):
        linkname = links_list[i]
        #print "linkname:", linkname
        realpath = os.readlink(linkname)
        if realpath.startswith(OLDPATH):
            newpath = realpath.replace(OLDPATH, NEWPATH)
            if os.path.islink(linkname) and os.path.isfile(newpath):
                os.remove(linkname)
                os.symlink(newpath, linkname)
                #print "oldpath:", realpath, "\n newpath:",  newpath
            
if __name__ == "__main__":
    OLDPATH = sys.argv[1]
    NEWPATH = sys.argv[2]
    src_dir = NEWPATH
    rewrite_links(src_dir, OLDPATH, NEWPATH)

