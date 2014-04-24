from django.conf.urls import patterns, url
from oseoserver import views

urlpatterns = patterns(
    '',
    #url(r'^server$', 'oseoserver.views.oseo_endpoint', name='oseo_endpoint'),
    #url(r'^orders/(?P<user_name>\w+)/(?P<order_id>\d+)/(?P<item_file_name>\w+\.?\w*)/$',
    #    'oseoserver.views.show_item', name='show_item'),
    url(r'^server$', views.oseo_endpoint, name='oseo_endpoint'),
    url(r'^orders/(?P<user_name>\w+)/(?P<order_id>\d+)/(?P<item_file_name>\w+\.?\w*)/$',
        views.show_item, name='show_item'),
)
