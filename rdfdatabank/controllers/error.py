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

import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request, response, tmpl_context as c
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from rdfdatabank.lib.base import BaseController, render
from rdfdatabank.lib.conneg import MimeType as MT, parse as conneg_parse

class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    def document(self):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        content = literal(resp.body) or cgi.escape(request.GET.get('message', ''))
        code = cgi.escape(request.GET.get('code', str(resp.status_int)))
        if 'HTTP_ACCEPT' in request.environ:
            try:
                accept_list = conneg_parse(request.environ['HTTP_ACCEPT'])
            except:
                accept_list= [MT("text", "plain")]
        if not accept_list:
            accept_list= [MT("text", "plain")]
        mimetype = accept_list.pop(0)
        while(mimetype):
            if str(mimetype).lower() in ["text/html", "text/xhtml"]:
                #page = error_document_template % \
                #dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                #    code=code,
                #    message=content)
                #return page
                c.code = code
                #c.message = content
                c.message = cgi.escape(request.GET.get('message', ''))
                c.status = resp.status
                c.status = c.status.replace(c.code, '').strip()
                if not c.message:
                    c.message = content.replace(resp.status, '').strip()
                return render('/error.html')
            elif str(mimetype).lower() in ["text/plain", "application/json"]:
                response.content_type = 'text/plain; charset="UTF-8"'
                response.status_int = resp.status_int
                response.status = resp.status
                return content
            try:
                mimetype = accept_list.pop(0)
            except IndexError:
                mimetype = None
        #Whoops nothing satisfies - return text/plain
        response.content_type = 'text/plain; charset="UTF-8"'
        response.status_int = resp.status_int
        response.status = resp.status
        return content

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
