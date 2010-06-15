_DATA = {
    'admin': {'first_name':'ben', 'last_name':'OSteen', 'owner':'*', 'role':'admin'},
    'admiral': {'name':'ADMIRAL Project', 'description':'ADMIRAL: A Data Management Infrastructure for Research', 'owner':['admiral'], 'role':'user'},
    'eidcsr': {'name':'EIDCSR Project', 'description':'The Embedding Institutional Data Curation Services in Research (EIDCSR) project is addressing the research data management and curation challenges of three research groups in the University of Oxford.', 'owner':['eidcsr'], 'role':'user'},
    }

class IdentMDProvider(object):

    def add_metadata(self, environ, identity):
        userid = identity.get('repoze.who.userid')
        info = _DATA.get(userid)
        if info is not None:
            identity.update(info)
