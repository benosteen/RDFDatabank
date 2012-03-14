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

# Add the virtual Python environment site-packages directory to the path
#import site
#site.addsitedir('/home/simplesite/env/lib/python2.5/site-packages')
#site.addsitedir('/usr/local/lib/python2.6/dist-packages')

import pkg_resources
pkg_resources.working_set.add_entry('/var/lib/databank')

# Avoid ``[Errno 13] Permission denied: '/var/www/.python-eggs'`` messages
import os
os.environ['PYTHON_EGG_CACHE'] = '/var/cache/databank/egg-cache'

# Load the Pylons application
from paste.deploy import loadapp
application = loadapp('config:/var/lib/databank/development.ini')

