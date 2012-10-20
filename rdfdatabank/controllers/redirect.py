# -*- coding: utf-8 -*-
import logging
from pylons import url

from pylons.controllers.util import redirect
from rdfdatabank.lib.base import BaseController

class RedirectController(BaseController):
    def index(self, id):
        if id.lower().endswith(('.html', '.rdf', '.json')):
            id = id.rsplit('.', 1)[0]
        lid = id.lower()
        if lid == 'dataset%3a1' or lid == 'dataset:1':
            redirect(url(controller="datasets", action="datasetview", silo="general", id='Tick1AudioCorpus'))
        elif lid == 'dataset%3A2.html' or lid == 'dataset:2':
            redirect(url(controller="datasets", action="datasetview", silo="general", id='RobertDarnton'))
        if lid == 'dataset%3A3' or lid == 'dataset:3':
            redirect(url(controller="datasets", action="datasetview", silo="general", id='MostynBrown'))
        else:
            redirect(url(controller="datasets", action="datasetview", silo="general", id=id))

