from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^oseo/', include('oseoserver.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^activity/', include('actstream.urls')),
    url(r'^orders/', include('giosystemdownloads.urls')),
)
