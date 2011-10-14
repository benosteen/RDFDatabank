import os
from rdfdatabank.lib.broadcast import BroadcastToRedis
from pylons import config

def get_objs_in_dir(items_list, dirname, fnames):
    for fname in fnames:
        a = os.path.join(dirname,fname)
        if fname == 'obj':
            item = a.split('pairtree_root')[1].strip('/').split('obj')[0].replace('/', '')
            silo = a.split('pairtree_root')[0].strip('/').split('/')[-1]
            if not (silo, item) in items_list:
                items_list.append((silo, item))
    return
    
def broadcast_links(src_dir):
    links_list = []
    os.path.walk(src_dir,get_objs_in_dir,links_list)
    b = BroadcastToRedis(config['redis.host'], config['broadcast.queue'])
    
    for silo, item in links_list:
        b.creation(silo, item)
    return
            
src_dirs = [
'/silos/admiral/pairtree_root',
'/silos/digitaltest/pairtree_root',
'/silos/eidcsr/pairtree_root',
'/silos/general/pairtree_root',
'/silos/ww1archives/pairtree_root',
'/silos/digitalbooks/pairtree_root/30',
'/silos/digitalbooks/pairtree_root/og/-4/00',
'/silos/digitalbooks/pairtree_root/og/-4/01',
'/silos/digitalbooks/pairtree_root/og/-3/00',
'/silos/digitalbooks/pairtree_root/og/-3/01',
'/silos/digitalbooks/pairtree_root/og/-3/02',
'/silos/digitalbooks/pairtree_root/og/-3/03',
'/silos/digitalbooks/pairtree_root/og/-3/04',
'/silos/digitalbooks/pairtree_root/og/-3/05',
'/silos/digitalbooks/pairtree_root/og/-3/06',
'/silos/digitalbooks/pairtree_root/og/-3/15',
'/silos/digitalbooks/pairtree_root/og/-3/16',
'/silos/digitalbooks/pairtree_root/og/-3/18',
'/silos/digitalbooks/pairtree_root/og/-3/20',
'/silos/digitalbooks/pairtree_root/og/-3/61',
'/silos/digitalbooks/pairtree_root/og/-3/90',
'/silos/digitalbooks/pairtree_root/og/-3/93',
'/silos/digitalbooks/pairtree_root/og/-5/00',
'/silos/digitalbooks/pairtree_root/og/-5/01',
'/silos/digitalbooks/pairtree_root/og/-5/02',
'/silos/digitalbooks/pairtree_root/og/-5/03',
'/silos/digitalbooks/pairtree_root/og/-5/04',
'/silos/digitalbooks/pairtree_root/og/-5/09', 
'/silos/digitalbooks/pairtree_root/og/-5/31', 
'/silos/digitalbooks/pairtree_root/og/-5/32', 
'/silos/digitalbooks/pairtree_root/og/-5/33', 
'/silos/digitalbooks/pairtree_root/og/-5/50', 
'/silos/digitalbooks/pairtree_root/og/-5/55', 
'/silos/digitalbooks/pairtree_root/og/-5/56', 
'/silos/digitalbooks/pairtree_root/og/-5/90', 
'/silos/digitalbooks/pairtree_root/og/-5/91', 
'/silos/digitalbooks/pairtree_root/og/-5/96', 
'/silos/digitalbooks/pairtree_root/og/-5/97',
'/silos/digitalbooks/pairtree_root/og/-6/00', 
'/silos/digitalbooks/pairtree_root/og/-6/50',
'/silos/digitalbooks/pairtree_root/og/-6/81',
'/silos/digitalbooks/pairtree_root/og/-6/90',
'/silos/digitalbooks/pairtree_root/og/-N/08',
'/silos/digitalbooks/pairtree_root/og/-N/10',
'/silos/digitalbooks/pairtree_root/og/-N/11',
'/silos/digitalbooks/pairtree_root/og/-N/12',
'/silos/digitalbooks/pairtree_root/og/-N/13',
'/silos/digitalbooks/pairtree_root/og/-N/14',
'/silos/digitalbooks/pairtree_root/og/-N/15',
'/silos/digitalbooks/pairtree_root/og/-N/16',
'/silos/digitalbooks/pairtree_root/og/-N/17',
'/silos/digitalbooks/pairtree_root/og/-N/32',
'/silos/digitalbooks/pairtree_root/og/-N/50'
]

for src_dir in src_dirs:
    print "starting", src_dir
    links_list = []
    os.path.walk(src_dir,get_objs_in_dir,links_list)
    b = BroadcastToRedis(config['redis.host'], config['broadcast.queue'])
    for silo, item in links_list:
        b.creation(silo, item)