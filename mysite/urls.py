# Copyright (C) 2019 Jorrit "Chainfire" Jongma
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hideyhole.urls')),
]

# Only serve static files from Django during development
# Use Google Cloud Storage or an alternative CDN for production
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
