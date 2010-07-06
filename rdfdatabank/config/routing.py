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

    map.redirect("/", "/silos")
    map.redirect('/*(url)/', '/{url}',
             _redirect_code='301 Moved Permanently')

    map.connect('/admin', controller='admin', action='index')
    map.connect('/admin/{silo_name}', controller='admin', action='archive')
    
    map.connect('/silos', controller='silos', action='index')

    map.connect('/{silo}', controller='silos', action='siloview')

    map.connect('/{silo}/packages', controller='packages', action='siloview')

    map.connect('/{silo}/datasets', controller='datasets', action='siloview')
    map.connect('/{silo}/datasets/{id}', controller='datasets', action='datasetview')
    map.connect('/{silo}/datasets/{id}/{path:.*}', controller='objects', action='itemview')

    map.connect('/{silo}/items', controller='items', action='siloview')
    map.connect('/{silo}/items/{id}', controller='items', action='datasetview')
    map.connect('/{silo}/items/{id}/{path:.*}', controller='items', action='itemview')
    
    map.connect('/{controller}')
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
