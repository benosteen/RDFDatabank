import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from pylons import app_globals as ag

from rdfdatabank.lib.base import BaseController, render

log = logging.getLogger(__name__)

class SearchController(BaseController):

    def raw(self):
        http_method = request.environ['REQUEST_METHOD']
        if http_method == "GET":
            params = request.GET
        elif http_method == "POST":
            params = request.POST
        if "q" in params and "wt" in params:
            result = ag.solr.raw_query(**params)
            if params['wt'] == "json":
                response.headers['Content-Type'] = 'application/json'
            elif params['wt'] == "xml":
                response.headers['Content-Type'] = 'text/xml'
            return result
        else:
            return render("/raw_search.html")
