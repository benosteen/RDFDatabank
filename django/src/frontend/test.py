
from django.http import HttpResponse

def index(request, siloname):
    return HttpResponse(siloname, mimetype="text/plain")
