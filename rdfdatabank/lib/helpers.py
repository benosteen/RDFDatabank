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
