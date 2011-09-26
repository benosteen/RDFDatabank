# -*- coding: utf-8 -*-
import logging

from rdfdatabank.lib.base import BaseController, render

class HomeController(BaseController):
    def index(self):
        return render('/home.html')
