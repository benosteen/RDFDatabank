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
        print "\nPATH INFO =", path_info, "\n"
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
