from pylons import url
from pylons import request, response, session, tmpl_context as c, url, app_globals as ag
from rdfdatabank.lib.base import BaseController, render
from pylons.controllers.util import abort, redirect
from paste.request import get_cookies
from webob.exc import HTTPUnauthorized

class AccountController(BaseController):
    def login(self):
        #c.ident = None
        #c.ident = request.environ.get('repoze.who.identity')
        #script_name = request.environ.get('SCRIPT_NAME') or '/'
        #referer = request.environ.get('HTTP_REFERER', script_name)

        #if not c.ident:
        #    abort(401, "Not Authorised")
        c.login_counter = request.environ['repoze.who.logins']
        if c.login_counter > 0:
            session['login_flash'] = """Wrong credentials. Have you registered? <a href="register">Register</a>"""
            session.save()
        c.came_from = request.params.get("came_from") or "/"
        return render('/login.html')

    def welcome(self):
        identity = request.environ.get("repoze.who.identity")
        came_from = request.params.get('came_from', '') or "/"
        came_from = str(came_from)
        if identity:
            # Login succeeded
            userid = identity['repoze.who.userid']
            #user_det = get_mediator_details(userid)
            #if user_det['name']:
            #    session['user_name'] = user_det['name']
            #if user_det['uri']:
            #    session['user_uri'] = str(user_det['uri'])
            session['user_id'] = userid
            session.save()
            return redirect(url(came_from))
        else:
            # Login failed
            try:
                login_counter = request.environ['repoze.who.logins'] + 1
            except:
                login_counter = 0
            destination = "/login?came_from=%s&logins=%s" % (came_from, login_counter)
            return redirect(url(destination))

    def logout(self):
        c.userid = None
        c.message = "We hope to see you soon!"
        #display_message("We hope to see you soon!", status="success")
        came_from = request.params.get('came_from', '') or "/"
        came_from = str(came_from)
        if session.has_key('user_name'):
            del session['user_name']
        if session.has_key('user_uri'):
            del session['user_uri']
        if session.has_key('user_id'):
            del session['user_id']
        if session.has_key('user_dept'):
            del session['user_dept']
        if session.has_key('user_email'):
            del session['user_email']
        session.save()
        #return render('/logout.html')
        return redirect(url(came_from))
