from django.conf.urls import patterns, url
from oseoserver import views

urlpatterns = patterns(
    '',
    url(r'^server$', views.oseo_endpoint, name='oseo_endpoint'),
    #url(r'^orders/(?P<user_name>\w+)/order_(?P<order_id>\d+)/(?P<item_id>\w+)/'
    #    '(?P<item_file_name>\w+\.?\w*)/$',
    #    views.show_item, name='show_item'),
    url(r'^orders/(?P<oseo_file_path>[\w/.]+)/$', views.show_item,
        name='show_item'),
)
