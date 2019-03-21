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

from rest_framework import serializers

from hideyhole.models import Wallpaper


class ImageFullSerializer(serializers.ModelSerializer):
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_width(self, obj):
        return obj.image_full_width

    def get_height(self, obj):
        return obj.image_full_height

    def get_url(self, obj):
        return obj.image_source_url

    class Meta:
        model = Wallpaper
        fields = (
            'width',
            'height',
            'url'
        )
        

class ImageThumbnailSerializer(ImageFullSerializer):
    def get_width(self, obj):
        return obj.image_thumbnail_width

    def get_height(self, obj):
        return obj.image_thumbnail_height

    def get_url(self, obj):
        return obj.image_thumbnail_url

    class Meta(ImageFullSerializer.Meta):
        pass


class WallpaperSerializer(serializers.ModelSerializer):
    added = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    popularity = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    def get_added(self, obj):
        return int(obj.added.timestamp())

    def get_source(self, obj):
        return obj.source_url

    def get_popularity(self, obj):
        return obj.popularity_total

    def get_image(self, obj):
        return ImageFullSerializer(obj).data

    def get_thumbnail(self, obj):
        return ImageThumbnailSerializer(obj).data

    class Meta:
        model = Wallpaper
        fields = (
            'id',
            'added',
            'author',
            'title',
            'category',
            'source',
            'popularity',
            'image',
            'thumbnail'
        )
