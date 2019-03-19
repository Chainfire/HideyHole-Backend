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

from django.db import models


class Wallpaper(models.Model):
    id = models.BigAutoField(primary_key=True)

    added = models.DateTimeField()

    author = models.CharField(max_length=128)
    title = models.CharField(max_length=128)
    category = models.CharField(max_length=32)

    popularity_source = models.IntegerField()
    popularity_app = models.IntegerField()
    popularity_total = models.IntegerField()

    source_url = models.CharField(max_length=256, unique=True)

    image_full_url = models.CharField(max_length=256)
    image_full_width = models.IntegerField()
    image_full_height = models.IntegerField()

    image_thumbnail_url = models.CharField(max_length=256)
    image_thumbnail_width = models.IntegerField()
    image_thumbnail_height = models.IntegerField()

    image_source_url = models.CharField(max_length=256, unique=True)
    image_source_sha1 = models.CharField(max_length=40, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['-added']),
            models.Index(fields=['-popularity_total'])
        ]


class BannedUrl(models.Model):
    url = models.CharField(max_length=256, unique=True)
