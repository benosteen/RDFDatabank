# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

import mimetools
import mimetypes

class MultiPartFormData(object):
    def __init__(self, fields=None, files=None):
        self._boundary = mimetools.choose_boundary()
        self._fields = fields or ()
        self._files = files or ()
        for file in self._files:
            file['mimetype'] = file.get('mimetype') or mimetypes.guess_type(file['filename'])[0] or 'application/octet-stream'
        self._body = self._body_iterator()
    
    @property
    def content_type(self):
        return 'multipart/form-data; boundary=%s' % self._boundary
    
    @property
    def content_length(self):
        field_padding = '--\r\nContent-Disposition: form-data; name=""\r\n\r\n\r\n'
        file_padding = '--\r\nContent-Disposition: form-data; name=""; filename=""\r\nContent-Type: \r\n\r\n'
        
        field_length = sum(sum(map(len, [self._boundary, field_padding, k, v])) for k,v in self._fields)
        file_length = sum(f['size'] + sum(map(len, [self._boundary, file_padding, f['name'], f['filename'], f['mimetype']])) for f in self._files)
        
        return field_length + file_length + len('----\r\n') + len(self._boundary)

    def _body_iterator(self):
        for (key, value) in self._fields:
            yield '--%s\r\n' % self._boundary
            yield 'Content-Disposition: form-data; name="%s"\r\n' % key
            yield '\r\n'
            if value:
                yield value
            yield '\r\n'
        for file in self._files:
            yield '--%s\r\n' % self._boundary
            yield 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (file['name'], file['filename'])
            yield 'Content-Type: %s\r\n' % file['mimetype']
            yield '\r\n'
            
            stream = file['stream']
            while True:
                data = stream.read(4096)
                if not data:
                    break
                yield data
        yield '--%s--\r\n' % self._boundary
    
    def read(self, blocksize):
        try:
            return self._body.next()
        except StopIteration:
            return ''
