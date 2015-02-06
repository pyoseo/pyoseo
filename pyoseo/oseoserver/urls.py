from django.conf.urls import patterns, url
from oseoserver import views

urlpatterns = patterns(
    '',
    url(r'^server$', views.oseo_endpoint, name='oseo_endpoint'),
)
