# Copyright (C) 2012 Eduardo Robles Elvira <edulix AT wadobo DOT com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *
from django.contrib.auth.views import login,logout
from agora_site.agora_core.views import TestView,Entry


urlpatterns = patterns('',
    (r'^test_view', TestView.as_view()),
    (r'^login', login, {'template_name': 'agora-core/login.html'}),
    (r'^logout', logout, {'next_page': '/'} ),
    (r'^entry', Entry.as_view()),
    
)
