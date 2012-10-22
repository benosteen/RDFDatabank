from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
        url(r'^$', 'frontend.silo.index', name='silo-index'),
        )

