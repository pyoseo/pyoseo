from django.conf.urls import patterns, url
from oseoserver import views

urlpatterns = patterns(
    '',
    url(r'^$', views.oseo_endpoint, name='oseo_endpoint'),
)
