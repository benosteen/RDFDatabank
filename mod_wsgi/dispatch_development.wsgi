# Add the virtual Python environment site-packages directory to the path
#import site
#site.addsitedir('/home/simplesite/env/lib/python2.5/site-packages')
#site.addsitedir('/usr/local/lib/python2.6/dist-packages')

import pkg_resources
pkg_resources.working_set.add_entry('/opt/RDFDatabank')

# Avoid ``[Errno 13] Permission denied: '/var/www/.python-eggs'`` messages
import os
os.environ['PYTHON_EGG_CACHE'] = '/opt/RDFDatabank/egg-cache'

# Load the Pylons application
from paste.deploy import loadapp
application = loadapp('config:/opt/RDFDatabank/development.ini')

