from django.conf.urls import patterns, url
from oseoserver import views

urlpatterns = patterns(
    '',
    url(r'^server$', views.oseo_endpoint, name='oseo_endpoint'),
    url(r'^orders/(?P<username>\w+)/(?P<order_id>\i+)/(?P<order_item_id>\i+)/$',
        views.oseo_endpoint, name='show_item'),
)
