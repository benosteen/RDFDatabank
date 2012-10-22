from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
        url(r'^$', 'frontend.views.api_index'),
        url(r'^(?P<api_name>[a-z]+)$', 'frontend.views.api_view'),
        )
