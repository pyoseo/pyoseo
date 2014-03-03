from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^oseo/', include('oseoserver.urls')),
    url(r'^products/', include('giosystem_webenabler.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
