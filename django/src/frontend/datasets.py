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

# HTTP Method restriction
from django.views.decorators.http import require_http_methods, require_safe
from django.http import Http404, HttpResponse, HttpResponseForbidden

from django.core.urlresolvers import reverse

# Mako templating engine
from djangomako.shortcuts import render_to_response, render_to_string

import settings

import json

from utils.filestore import granary
from utils.redis_helper import b
from utils.file_unpack import check_file_mimetype, BadZipfile, get_zipfiles_in_dataset, unpack_zip_item, read_zipfile

from utils.misc import create_new, allowable_id2

from utils.auth_entry import list_silos, get_datasets_count, authz, add_auth_info_to_context, list_user_permissions, \
                             add_dataset, delete_dataset, get_datasets_count, get_datasets
from utils.conneg import MimeType as MT, parse as conneg_parse
from utils.bag import Context

import logging
log = logging.getLogger(__name__)


def silo_view(request, siloname):
    return HttpResponse(siloname, mimetype="text/plain")
    
def dataset_view(request, siloname, id):
    return HttpResponse(siloname+" "+id, mimetype="text/plain")
    
def item_view(request, siloname, id, path):
    return HttpResponse(siloname+" "+id+" - "+path, mimetype="text/plain")
