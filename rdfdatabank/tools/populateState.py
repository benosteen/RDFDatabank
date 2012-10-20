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

import os
import simplejson
from pylons import config

def get_objs_in_dir(items_in_silo, dirname, fnames):
    for fname in fnames:
        a = os.path.join(dirname,fname)
        if fname == 'obj':
            item = a.split('pairtree_root')[1].strip('/').split('obj')[0].replace('/', '')
            silo = a.split('pairtree_root')[0].strip('/').split('/')[-1]
            if not silo in items_in_silo:
                items_in_silo[silo] = set()
            items_in_silo[silo].add(item)
    return
    
def update_silo_persisted_state(root_dir, src_dir):
    silo_items = {}
    os.path.walk(src_dir,get_objs_in_dir,silo_items)
    for silo, items in silo_items.iteritems():
        filepath = "%s/%s/persisted_state.json"%(root_dir, silo)
        if not os.path.isfile(filepath):
            print "File %s does not exist"%filepath
            return
        with open(filepath, "r") as serialised_file:
            state = simplejson.load(serialised_file)
        state['items'] = list(items)
        state['item_count'] = "%d"%len(state['items'])
        with open(filepath, "w") as serialised_file:
            simplejson.dump(state, serialised_file)
    return

if __name__ == '__main__':         
    src_dirs = [
      '/silos/loadtest'
    ]
    root_dir = '/silos'
    for src_dir in src_dirs:
        print "starting", src_dir
        update_silo_persisted_state(root_dir, src_dir)
