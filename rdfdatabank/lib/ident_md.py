from rdfdatabank.config.users import _USERS as _DATA

class IdentMDProvider(object):

    def add_metadata(self, environ, identity):
        userid = identity.get('repoze.who.userid')
        info = _DATA.get(userid)
        if info is not None:
            identity.update(info)
