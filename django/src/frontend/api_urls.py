from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
        url(r'^$', 'frontend.silo.view', name='silo-view'),
        # Silo State
        url(r'state/$', 'frontend.state.silo_view', name='silo-state'),
        url(r'state/(?P<id>[0-9A-z\-\:]+)/$', 'frontend.state.dataset_view'),
        # Items
        url(r'items/$', 'frontend.items.silo_view', name="items_siloview"),
        url(r'items/(?P<id>[0-9A-z\-\:]+)/$', 'frontend.items.dataset_view', name="dataset_view"),
        url(r'items/(?P<id>[0-9A-z\-\:]+)/(?P<path>[a-zA-Z0-9_\-\:\.]+)$', 'frontend.items.item_view', name="item_view"),
        url(r'items/(?P<id>[0-9A-z\-\:]+)/(?P<path>[a-zA-Z0-9_\-\:\.]+)/(?P<subpath>.+)$', 'frontend.items.subitem_view', name="subitem_view"),
        # Datasets
        url(r'datasets/$', 'frontend.datasets.silo_view', name="datasets_silo_view"),
        url(r'datasets/(?P<id>[0-9A-z\-\:]+)/$', 'frontend.datasets.dataset_view', name="datasets_main_view"),
        url(r'datasets/(?P<id>[0-9A-z\-\:]+)/(?P<path>[a-zA-Z0-9_\-\:\.]+)$', 'frontend.datasets.item_view', name="datasets_item_view"),
        )

