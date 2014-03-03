from django.conf.urls import patterns, url
from giosystem_webenabler import views

urlpatterns = patterns(
    '',
    url(r'^(?P<product>\w+)/(?P<timeslot>\d{12})/$', views.get_product,
        name='get_product'),
    url(r'^(?P<product>\w+)/(?P<timeslot>\d{12})/(?P<tile>\w+)/$',
        views.get_product, name='get_product'),
    url(r'^quicklooks/(?P<product>\w+)/(?P<timeslot>\d{12})/$', views.get_quicklook,
        name='get_quicklook'),
    url(r'^wms/(?P<product>\w+)/$', views.get_wms, name='get_quicklook'),
)
