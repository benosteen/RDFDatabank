import sqlalchemy as sa
from rdfdatabank.model import init_model
from rdfdatabank.lib.auth_entry import add_user, add_user_groups
import ConfigParser
import sys, os

if __name__ == "__main__":
    #Initialize sqlalchemy
    c = ConfigParser.ConfigParser()
    f = '/var/lib/databank/production.ini' 
    c.read(f)
    if not os.path.exists(f):
        print "Config file not found"
    elif not 'app:main' in c.sections():
        print "Section app:main not found in config file"
    else:
        engine = sa.create_engine(c.get('app:main', 'sqlalchemy.url'))
        init_model(engine)
        #add user
        username = sys.argv[1]
        password = sys.argv[2]
        email = sys.argv[3]
        user_details = {
        'username':u'%s'%username,
        'password':u"%s"%password,
        'name':u'Databank Administrator',
        'email':u"%s"%email
        }
        add_user(user_details)
        #Add user membership
        groups = []
        groups.append(('*', 'administrator'))
        add_user_groups(username, groups)

