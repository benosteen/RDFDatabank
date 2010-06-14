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
    map.redirect("/", "/objects")

    map.connect('/packages', controller='packages', action='index')
    map.connect('/packages/{silo}', controller='packages', action='siloview')
    map.connect('/packages/{silo}/upload', controller='packages', action='upload')
    map.connect('/objects', controller='objects', action='index')
    map.connect('/objects/{silo}', controller='objects', action='siloview')
    map.connect('/objects/{silo}/{id}', controller='objects', action='itemview')
    map.connect('/objects/{silo}/{id}/{path:.*}', controller='objects', action='subitemview')
    
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')
    
    map.redirect('/*(url)/', '/{url}',
             _redirect_code='301 Moved Permanently')

    return map
