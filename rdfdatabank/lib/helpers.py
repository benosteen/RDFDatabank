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

"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
from webhelpers.date import *
from webhelpers.text import *
from webhelpers.html.converters import *
from webhelpers.html.tools import *
from webhelpers.util import *
from routes import url_for

from rdfdatabank.lib.conneg import parse as conneg_parse

def bytes_to_english(no_of_bytes):
    # 1024 per 'level'
    suffixes = ['bytes', 'kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb', 'Yb']
    f_no = float(no_of_bytes)
    level = 0
    while(f_no > 1024.0):
        f_no = f_no / 1024.0
        level = level + 1
    if level == 0:
        return "%s %s" % (no_of_bytes, suffixes[level])
    return "%5.1f %s" % (f_no, suffixes[level])
