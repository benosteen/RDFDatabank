#-*- coding: utf-8 -*-
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

"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE

    map.redirect('/*(url)/', '/{url}',
             _redirect_code='301 Moved Permanently')

    #Special controller to redirect datasets from databank.ouls to databank.ora
    #map.connect('/objects/{id}', controller='redirect', action='index')

    map.connect("/login", controller='account', action='login')
    map.connect("/logout", controller='account', action='logout')
    map.connect("/welcome", controller='account', action='welcome')

    map.connect('/', controller='home', action='index')
    map.connect('/api', controller='api', action='index')
    map.connect('/api/{api_name}', controller='api', action='apiview')
   
    map.connect('/keywords', controller='keywords', action='index')
    map.connect('/about', controller='about', action='index')
    map.connect('/searching', controller='searching', action='index')

    map.connect('/admin', controller='admin', action='index')
    map.connect('/users', controller='users', action='index')
    map.connect('/users/{username}', controller='users', action='userview')
    map.connect('/{silo}/users', controller='users', action='siloview')
    map.connect('/{silo}/users/{username}', controller='users', action='silouserview')
    map.connect('/{silo}/admin', controller='admin', action='siloview')
    
    map.connect('/silos', controller='silos', action='index')
    map.connect('/{silo}', controller='silos', action='siloview')

    map.connect('/{silo}/datasets', controller='datasets', action='siloview')
    map.connect('/{silo}/datasets/{id}', controller='datasets', action='datasetview')
    map.connect('/{silo}/datasets/{id}/{path:.*}', controller='datasets', action='itemview')

    map.connect('/{silo}/items', controller='items', action='siloview')
    map.connect('/{silo}/items/{id}', controller='items', action='datasetview')
    map.connect('/{silo}/items/{id}/{path:.*?\.zip}', controller='items', action='itemview')
    map.connect('/{silo}/items/{id}/{path:.*?\.zip}/{subpath:.*}', controller='items', action='subitemview')
    #map.connect('/{silo}/items/{id}/{path:.*}', controller='items', action='itemview') # Use verb dataset instead
    
    map.connect('/{silo}/states', controller='states', action='siloview')
    map.connect('/{silo}/states/{id}', controller='states', action='datasetview')
    
    map.connect('/{silo}/doi/{id}', controller='doi', action='datasetview')

    # SWORDv2 Configuration
    map.connect('/swordv2/service-document', controller="sword", action="service_document") # From which to retrieve the service document
    map.connect('/swordv2/silo/{path:.*?}', controller="sword", action="collection") # Representing a Collection as listed in the service document
    map.connect('/swordv2/edit-media/{path:.*?}', controller="sword", action="media_resource") # The URI used in atom:link@rel=edit-media
    map.connect('/swordv2/edit/{path:.*?}', controller="sword", action="container") # The URI used in atom:link@rel=edit
    map.connect('/swordv2/statement/{path:.*?}', controller="sword", action="statement") # The URI used in atom:link@rel=sword:statement

    map.connect('/{controller}')
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
