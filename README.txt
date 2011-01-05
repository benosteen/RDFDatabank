RDF Databank

Overview
========

RDF-enhanced storage API, pairtree-backed.

Installation and dependancies
=============================

-  [I would advise using virtualenv]

Dependancies:

pylons==0.9.7
pairtree==0.5.6-T
rdfobject
recordsilo
simplejson
solrpy

redis (use the redis client that is compatible with your redis server - http://github.com/andymccurdy/redis-py/)


-  Change the settings in development.ini to suit your uses, specifically:

redis.host = localhost

granary.store = silos  # Directory to storage directory. Can be absolute: /var/silos
granary.uri_root = http://databank.bodleian.ox.ac.uk/objects/ # URI root - must end with /, # or :

broadcast.to = redis    
broadcast.queue = silochanges  # redis 'queue' to push audit messages to (create, delete, update or embargo change)

solr.host = http://localhost:8983/solr   # Unset this to ignore solr while testing

Setup:
======

Create a file 'passwd' in the root directory of the application using 'htpasswd' or similar:

$ htpasswd -c passwd admin
[enter admin password]

Add any users you wish to access or work with this application.

Edit ./rdfdatabank/lib/ident_md.py - this has a variable _DATA which would best be replaced by a DB lookup or similar. For now, adjust it
to suit your users - the important thing is the 'role'.

Start up the redis-server and confirm that you can access it.

You should be able to start the application now (as long as the application has access to r+w to the aforementioned 'silos' directory.)

paster serve development.ini

Then, go to localhost:5000/admin, and try to log in as the 'admin' account. You should then be able to create and manage silos and assign write-access to them to users.

WGSI deployment:
================

Copy 'development.ini' to a file called 'production.ini' and make sure debug = false and that the 'silos' directory is
owned by the web-server user (www-data for example). Recommendation is to have a separate silo directory for production use.

Create a folder called 'egg-cache' and make sure that is writable by the web-server user too.

Create a folder 'mod_wsgi' in the root of the application.

Create a file within that called 'dispatch.wsgi' and put in the following:

---------------
# Add the virtual Python environment site-packages directory to the path

import pkg_resources
pkg_resources.working_set.add_entry('/opt/rdfdatabank/src')    # Path to application root

# Avoid ``[Errno 13] Permission denied: '/var/www/.python-eggs'`` messages
import os
os.environ['PYTHON_EGG_CACHE'] = '/opt/rdfdatabank/src/egg-cache'   # Path to writable directory for egg-cache

# Load the Pylons application
from paste.deploy import loadapp
application = loadapp('config:/opt/rdfdatabank/src/production.ini')  #  Path to production.ini file

---------------

In your apache2 configuration, you need an entry like:

<VirtualHost *:80>
    ServerName foo.com

    # Logfiles
    ErrorLog  /opt/rdfdatabank/apachelog/error.log
    CustomLog /opt/rdfdatabank/apachelog/access.log combined
 
    # Use only 1 Python sub-interpreter.  Multiple sub-interpreters
    # play badly with C extensions.
    WSGIApplicationGroup %{GLOBAL}
    WSGIPassAuthorization On
    # Setup mod_wsgi
    WSGIScriptAlias / /opt/rdfdatabank/src/mod_wsgi/dispatch.wsgi

    <Directory /opt/rdfdatabank/src/mod_wsgi>
    Order deny,allow
    Allow from all
    </Directory>

</VirtualHost>

Note the WSGIScriptAlias points to the dispatch.wsgi file.

---------------

Note about permissions:
src directory and all its files and directories:
    Set the owner as admin_user:www-data
    Set the permission to 775 on all directories and everything under it
    set the owner as www-data:www-data for src/data folder
    Set the permission to 644 on all files
apachelog directory and all its files and directories:
    Set the owner as admin_user:www-data
    Set the persmissions 755 (currently the dir permission is set to 755 and the permission of the files within it is set to 644)
All of other directories:
    Set the owner as admin_user:admin_user
    Set the permission to 775 on all directories and everything under it

