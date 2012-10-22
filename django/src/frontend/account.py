# HTTP Method restriction
from django.views.decorators.http import require_http_methods, require_safe
from django.http import Http404, HttpResponse, HttpResponseForbidden

from django.shortcuts import redirect

# Mako templating engine
from djangomako.shortcuts import render_to_response, render_to_string

import settings

import json

from utils.filestore import granary
from utils.solr_helper import getSiloModifiedDate
from utils.redis_helper import r, b
from utils.misc import is_embargoed

from utils.auth_entry import get_datasets_count, get_datasets, authz, add_auth_info_to_context
from utils.conneg import MimeType as MT, parse as conneg_parse
from utils.bag import Context

from django.contrib.auth import login, authenticate, logout

import logging
log = logging.getLogger(__name__)

def login_handler(request):
    c = Context()   # duck-typed context object for Mako
    c.came_from = request.GET.get('came_from', "/")
    
    if request.method == "POST":
        if request.POST.has_key('login') and request.POST.has_key('password'):
            username = request.POST['login']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Redirect to a success page.
                    return redirect('/welcome')
                else:
                    # Return a 'disabled account' error message
                    request.session['login_flash'] = """Your account is currently disabled. Please contact the administrator."""
            else:
                # Return an 'invalid login' error message.
                request.session['login_flash'] = """Wrong credentials. Have you been registered?"""
    
    return render_to_response("login.html", {'c':c, 'request':request})

def welcome(request):
    c = Context()   # duck-typed context object for Mako
    c.came_from = request.GET.get('came_from', "/")
    c.ident = request.user
    if request.user.is_authenticated():
        add_auth_info_to_context(request, c)
        request.session['user_id'] = request.user.username
        return redirect(c.came_from)
    else:
        destination = "/login?came_from=%s" % (c.came_from)
        return redirect(destination)

def logout_handler(request):
    logout(request)
    came_from = request.GET.get('came_from', "/")
    return redirect(came_from)
