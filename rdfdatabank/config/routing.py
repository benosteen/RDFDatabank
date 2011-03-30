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

    #map.redirect("/", "/silos")
    map.redirect('/*(url)/', '/{url}',
             _redirect_code='301 Moved Permanently')

    #Special controller to redirect datasets from databank.ouls to databank.ora
    map.connect('/objects/{id}', controller='redirect', action='index')

    map.connect('/', controller='home', action='index')
    map.connect('/api', controller='api', action='index')
    map.connect('/api/{api_name}', controller='api', action='apiview')
   
    map.connect('/admin', controller='admin', action='index')
    map.connect('/{silo_name}/admin', controller='admin', action='archive')
    map.connect('/{silo_name}/register', controller='admin', action='register')
    
    map.connect('/silos', controller='silos', action='index')
    map.connect('/{silo}', controller='silos', action='siloview')

    map.connect('/{silo}/datasets', controller='datasets', action='siloview')
    map.connect('/{silo}/datasets/{id}', controller='datasets', action='datasetview')
    map.connect('/{silo}/datasets/{id}/version{vnum}', controller='datasets', action='datasetview_vnum')
    map.connect('/{silo}/datasets/{id}/{path:.*}/version{vnum}', controller='datasets', action='itemview_vnum')
    map.connect('/{silo}/datasets/{id}/{path:.*}', controller='datasets', action='itemview')

    map.connect('/{silo}/items', controller='items', action='siloview')
    map.connect('/{silo}/items/{id}', controller='items', action='datasetview')
    map.connect('/{silo}/items/{id}/{path:.*?\.zip}', controller='items', action='itemview')
    map.connect('/{silo}/items/{id}/{path:.*?\.zip}/{subpath:.*}', controller='items', action='subitemview')
    #map.connect('/{silo}/items/{id}/{path:.*}', controller='items', action='itemview') # Use verb dataset instead
    
    map.connect('/{silo}/states', controller='states', action='siloview')
    map.connect('/{silo}/states/{id}', controller='states', action='datasetview')
    map.connect('/{silo}/states/{id}/version{vnum}', controller='states', action='datasetview_vnum')
    
    map.connect('/{silo}/doi/{id}', controller='doi', action='datasetview')

    map.connect('/{controller}')
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
