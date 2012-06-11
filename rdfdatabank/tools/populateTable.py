import sqlalchemy as sa
import ConfigParser, os
from rdfdatabank import model
from rdfdatabank.lib.auth_entry import add_dataset

class populateTable:

    def __init__(self, configFile="/var/lib/databank/production.ini"):
        Config = ConfigParser.ConfigParser()
        Config.read("/var/lib/databank/production.ini")
        db_conn = Config.get("app:main", "sqlalchemy.url")
        self.root_dir = Config.get("app:main", "granary.store")
        engine = sa.create_engine(db_conn)
        model.init_model(engine)

    def add_objs_in_dir(self, items_in_silo, dirname, fnames):
        for fname in fnames:
            a = os.path.join(dirname,fname)
            if fname == 'obj':
                item = a.split('pairtree_root')[1].strip('/').split('obj')[0].replace('/', '')
                silo = a.split('pairtree_root')[0].strip('/').split('/')[-1]
                add_dataset(silo, item)
        return

    def populate(self):
        silo_items = {}
        os.path.walk(self.root_dir,self.add_objs_in_dir,silo_items)


if __name__ == '__main__':
    p = populateTable()
    p.populate()
