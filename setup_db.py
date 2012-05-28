import sqlalchemy as sa
from rdfdatabank.model import init_model
from rdfdatabank.lib.auth_entry import add_user, add_user_groups, add_silo
import ConfigParser
import sys, os

class setupDB():

    def __init__(self, config_file='/var/lib/databank/production.ini'):
        if not os.path.exists(config_file):
            print "Config file not found"
            sys.exit()
        c = ConfigParser.ConfigParser()
        c.read(config_file)
        if not 'app:main' in c.sections():
            print "Section app:main not found in config file"
            sys.exit()
        engine = sa.create_engine(c.get('app:main', 'sqlalchemy.url'))
        init_model(engine)
        return

    def addUser(self, user_details):
        if not ('username' in user_details and user_details['username'] and \
                'password' in user_details and user_details['password'] and \
               ('name' in user_details and user_details['name'] or \
               ('firstname' in user_details and user_details['firstname'] and \
               'lastname' in user_details and user_details['lastname']))):
            return False
        add_user(user_details)
        return True

    def addSilo(self, silo):
        add_silo(silo)
        return 

    def addUserGroup(self, username, silo, permission):
        groups = []
        groups.append((silo, permission))
        add_user_groups(username, groups)
        return 

if __name__ == "__main__":
    #Initialize sqlalchemy
    s = setupDB()

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
    s.addUser(user_details)

    #Add user membership
    s.addUserGroup(username, '*', 'administrator')

