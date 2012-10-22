from django.shortcuts import redirect

from utils.bag import Context
from utils.auth_entry import list_silos, get_datasets_count, authz, add_auth_info_to_context
from djangomako.shortcuts import render_to_response, render_to_string

def home(request):
    # logged in user
    c = Context()   # duck-typed context object for Mako
    c.ident = request.user
    add_auth_info_to_context(request, c)
    return render_to_response("home.html", {'c':c})

def api_index(request):
    # logged in user
    c = Context()   # duck-typed context object for Mako
    c.ident = request.user
    return redirect("/api/silos")
    
def api_view(request, api_name):
    # logged in user
    c = Context()   # duck-typed context object for Mako
    c.ident = request.user
    add_auth_info_to_context(request, c)
    if api_name not in ['silos', 'datasets', 'states', 'items']:
        # redirect(url(controller="api", action="apiview", api_name="silos"))
        return redirect("/api/silos")
    c.api_file = "%s_api.html"%api_name    
    return render_to_response('/api.html', {'c':c})
