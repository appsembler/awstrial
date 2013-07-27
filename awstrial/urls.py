#    AWSTrial, A mechanism and service for offering a cloud image trial
#
#    Copyright (C) 2010  Scott Moser <smoser@ubuntu.com>
#    Copyright (C) 2010  Dave Walker (Daviey) <DaveWalker@ubuntu.com>
#    Copyright (C) 2010  Michael Hall <mhall119@gmail.com>
#    Copyright (C) 2010  Dustin Kirkland <kirkland@ubuntu.com>
#    Copyright (C) 2010  Andreas Hasenack <andreas@canonical.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from django.conf.urls.defaults import *
from django.conf import settings
import ubuntu_website
from adminaudit import audit_install

from django.contrib import admin
admin.autodiscover()
audit_install()

###
# When starting this Django project, update the default Site object
# (http://stackoverflow.com/questions/2095155/django-app-initalization-code-
# like-connecting-to-signals)
# Note that at least one Site instance exists after syncdb, so there's no need
# to create anything here:
# https://code.djangoproject.com/browser/django/tags/releases/1.3/django/contri
# b/sites/management.py
from django.contrib.sites.models import Site
Site.objects.update(
    domain=settings.DEFAULT_SITE_DOMAIN, name=settings.DEFAULT_SITE_NAME)


urlpatterns = patterns('',
    (r'^$', 'trial.views.index'),
    (r'^(?P<campaign>[a-zA-Z0-9\-\.\+?]+)/running/', 'trial.views.reserved_instance'),
    (r'^(?P<campaign>[a-zA-Z0-9\-\.\+?]+)/start/', 'trial.views.start'),
    (r'^(?P<campaign>[a-zA-Z0-9\-\.\+?]+)/run/', 'trial.views.run_instance'),
    (r'^(?P<campaign>[a-zA-Z0-9\-\.\+?]+)/instance_info/', 'trial.views.info_instance'),

    (r'^feedback/', 'trial.views.feedback'),

    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('allauth.urls')),
    #(r'^openid/', include('django_openid_auth.urls')),
    #(r'^logout/$', 'trial.views.logout_view'),

    (r'^info_callback/(?P<secret>[a-zA-Z0-9]+)/(?P<mode>[a-zA-Z0-9]+)/', 'trial.info_callback.info_callback'),
    (r'^faq/', 'django.views.generic.simple.direct_to_template', {'template': 'faq.html'}),
    (r'^account-problem/', 'django.views.generic.simple.direct_to_template', {'template': 'account-problem.html'}),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
        (r'^(robots.txt)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
        (r'^ubuntu-website/media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': ubuntu_website.MEDIA_ROOT}),
    )
