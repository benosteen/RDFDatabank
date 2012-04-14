from rdfdatabank.lib.auth_entry import add_user, add_user_groups
import sys

if __name__ == "__main__":
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

    groups = []
    groups.append(('*', 'administrator'))
    add_user_groups(groups)

