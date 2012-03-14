# -*- coding: utf-8 -*-
"""
Copyright (c) 2012 University of Oxford

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from webob import Request
import zope.interface
from repoze.who.classifiers import default_request_classifier
from repoze.who.interfaces import IRequestClassifier
import ConfigParser
from pylons import config

def custom_request_classifier(environ):
    """ Returns one of the classifiers 'app', 'browser' or any
    standard classifiers returned by
    repoze.who.classifiers:default_request_classifier
    """


    classifier = default_request_classifier(environ)
    if classifier == 'browser':
        login_form_url = '/login'
        login_handler = '/login_handler'
        logout_handler = '/logout_handler'
        logout_url = '/logout'
        # Decide if the client is a (user-driven) browser or an application
        if config.has_key("who.config_file"):
            config_file = config["who.config_file"]
            config_who = ConfigParser.ConfigParser()
            config_who.readfp(open(config_file))
            login_form_url = config_who.get("plugin:friendlyform", "login_form_url")
            login_handler = config_who.get("plugin:friendlyform", "login_handler_path")
            logout_handler = config_who.get("plugin:friendlyform", "logout_handler_path")
            logout_url = config_who.get("plugin:friendlyform", "post_logout_url")

        path_info = environ['PATH_INFO']
        #request = Request(environ)
        #if not request.accept.best_match(['application/xhtml+xml', 'text/html']):
        #    # In our view, any client who doesn't support HTML/XHTML is an "app",
        #    #   not a (user-driven) "browser".
        #    classifier = 'app'
        if not path_info in [login_form_url, login_handler, logout_handler, logout_url]:
            # In our view, any client who hasn't come in from the login url is an app
            classifier = 'app'
    return classifier
zope.interface.directlyProvides(custom_request_classifier, IRequestClassifier)
