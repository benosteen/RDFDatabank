import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import app_globals as ag
from rdfdatabank.lib.base import BaseController, render

class ApiController(BaseController):
    def index(self):
        redirect_to(controller="api", action="apiview", api_name="silos")

    def apiview(self, api_name):
        if api_name not in ['silos', 'datasets', 'states', 'items']:
            redirect_to(controller="api", action="apiview", api_name="silos")
        c.api_file = "%s_api.html"%api_name    
        return render('/api.html')
