from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'databank.views.home', name='home'),
    # url(r'^databank/', include('databank.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^$', 'frontend.views.home', name='home'),
    url(r'^login$', 'frontend.account.login_handler', name='login'),
    url(r'^login_handler$', 'frontend.account.login_handler', name='login'),
    url(r'^logout$', 'frontend.account.logout_handler', name='logout'),
    url(r'^logout_handler$', 'frontend.account.logout_handler', name='logout'),
    url(r'^welcome$', 'frontend.account.welcome', name='welcome'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^silos/', include('frontend.silo_urls')),
    url(r'^api/', include('frontend.api_doc_urls')),
    url(r'^(?P<siloname>[a-zA-Z]+)/', include('frontend.api_urls')),
)
