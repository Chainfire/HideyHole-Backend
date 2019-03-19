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

from django.http import HttpResponse
from django.db.models import F

from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response

from hideyhole.models import Wallpaper
from hideyhole.serializers import WallpaperSerializer


def index(request):
    return HttpResponse('This the home of the Hidey Hole backend. You probably want the <a href="https://play.google.com/store/apps/details?id=eu.chainfire.hideyhole">app</a> or the <a href="https://www.reddit.com/r/S10wallpapers/comments/b1ydyh/hidey_hole_an_app_for_this_sub/">Reddit thread</a>.')


class WallpaperPagination(PageNumberPagination):
    page_size = 50


class WallpaperList(generics.ListAPIView):
    # /api/v1/wallpapers?device=*&category=*&sort=popular

    serializer_class = WallpaperSerializer
    pagination_class = WallpaperPagination

    def get_queryset(self):
        qs = Wallpaper.objects.all()

        device = self.request.query_params.get('device', '*')
        if device != '*':
            #TODO do this without hardcoding the values
            devices = ['s10_cutout', 's10e_cutout', 's10plus_cutout']
            if device + '_cutout' in devices:
                devices.remove(device + '_cutout')
            qs = qs.exclude(category__in=devices)

        category = self.request.query_params.get('category', '*')
        if category != '*':
            if category == '*cutout':
                qs = qs.filter(category__endswith='cutout')
            else:
                qs = qs.filter(category=category)

        sort = self.request.query_params.get('sort', 'popular')
        if sort == 'new':
            qs = qs.order_by('-added')
        else:
            qs = qs.order_by('-popularity_total')

        return qs


@api_view(['PUT'])
def wallpaper_upvote(request):
    id = request.query_params.get('id', False)
    if not id:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if id:
        Wallpaper.objects.filter(id=id).update(popularity_app=F('popularity_app') + 1)
        Wallpaper.objects.filter(id=id).update(popularity_total=(F('popularity_app') * 10 + F('popularity_source')))
        return Response(status=status.HTTP_200_OK)
