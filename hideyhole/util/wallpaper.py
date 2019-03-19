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

import os
import io
import requests
import hashlib
import datetime

from PIL import Image
from google.cloud import storage

from mysite.settings import SCRAPED_IMAGES_BUCKET
from hideyhole.models import BannedUrl, Wallpaper


__client = None
__bucket = None


# this is only called from cron/shell scripts that should continue, hence the odd error handling
def save_scraped_wallpaper(author, title, category, popularity, source_url, image_url, added):
    global __client, __bucket

    if not image_url.lower().endswith('.jpg') and not image_url.lower().endswith('.png'):
        print("FAIL [%s] does not end with [.jpg|.png]" % source_url)
        return

    if BannedUrl.objects.filter(url__in=[source_url, image_url]).exists():
        print("FAIL [%s] source_url or image_url banned" % source_url)
        return

    existing = Wallpaper.objects.filter(source_url=source_url)
    if len(existing) > 0:
        existing[0].popularity_source = popularity
        existing[0].popularity_total = existing[0].popularity_source + (existing[0].popularity_app * 10)
        existing[0].category = category
        existing[0].save()
        print("FAIL [%s] Wallpaper already exists [source_url]" % source_url)
        return

    existing = Wallpaper.objects.filter(image_source_url=image_url)
    if len(existing) > 0:
        if popularity > existing[0].popularity_source:
            existing[0].popularity_source = popularity
            existing[0].popularity_total = existing[0].popularity_source + (existing[0].popularity_app * 10)
            existing[0].save()
        print("FAIL [%s] Wallpaper already exists [image_url]" % source_url)
        return

    image_request = requests.get(image_url)
    if image_request.status_code != 200:
        print("FAIL [%s] download [%s] failed [%d]" % (source_url, image_url, image_request.status_code))
        return

    sha1 = hashlib.sha1(image_request.content).hexdigest()

    existing = Wallpaper.objects.filter(image_source_sha1=sha1)
    if len(existing) > 0:
        if popularity > existing[0].popularity_source:
            existing[0].popularity_source = popularity
            existing[0].popularity_total = existing[0].popularity_source + (existing[0].popularity_app * 10)
            existing[0].save()
        print("FAIL [%s] Wallpaper already exists [sha1]" % source_url)
        return

    try:
        im = Image.open(io.BytesIO(image_request.content))
    except:
        print("FAIL [%s] Image decode failed" % source_url)
        return

    png = False
    if im.mode == 'RGBA' or im.mode == 'LA' or im.mode == 'P' or image_url.endswith('.png'):
        png = True
    filename = sha1 + ('.png' if png else '.jpg')
    filename_full = 'images/' + filename
    filename_thumb = 'thumbnails/' + filename
    image_full_bytes = image_request.content

    width, height = im.size
    if not 2.10 <= height / width <= 2.12 or width < 640:
        print("FAIL [%s] Aspect ratio [%.2f] or width [%d]" % (source_url, height / width, width))
        # let's not download this image again
        BannedUrl(url=image_url).save()
        return

    try:
        thumb = Image.open(io.BytesIO(image_request.content))
        thumb.thumbnail((360, 760), Image.LANCZOS)
        with io.BytesIO() as output:
            if png:
                thumb.save(output, "PNG")
            else:
                thumb.save(output, "JPEG", quality=80)
            image_thumb_bytes = output.getvalue()
    except:
        print("FAIL [%s] Thumbnail create fail" % source_url)
        return

    # Google Cloud Storage
    try:
        if __client is None:
            storage_account = os.getenv('CLOUDSTORAGE_SERVICE_ACCOUNT_JSON')
            if storage_account:
                __client = storage.Client.from_service_account_json(storage_account)
            else:
                __client = storage.Client()
        if __client is None:
            print("FAIL [%s] Could not create Cloud Storage Client" % source_url)
            return

        if __bucket is None:
            __bucket = __client.bucket(SCRAPED_IMAGES_BUCKET)
        if __bucket is None:
            print("FAIL [%s] Could not create Cloud Storage Bucket" % source_url)
            return

        blob = __bucket.blob(filename_full)
        if blob.exists():
            __bucket.delete_blob(filename_full)
        blob.upload_from_string(image_full_bytes, 'image/png' if png else 'image/jpeg')

        blob = __bucket.blob(filename_thumb)
        if blob.exists():
            __bucket.delete_blob(filename_thumb)
        blob.upload_from_string(image_thumb_bytes, 'image/png' if png else 'image/jpeg')
    except Exception as e:
        print("FAIL [%s] Unexpected issue saving to Google Cloud Storage [%s]" % (source_url, str(e)))
        return

    try:
        Wallpaper(
            added=datetime.datetime.fromtimestamp(added, tz=datetime.timezone.utc),
            author=author,
            title=title,
            category=category,
            popularity_source=popularity,
            popularity_app=0,
            popularity_total=popularity,
            source_url=source_url,
            image_full_url='https://storage.googleapis.com/%s/%s' % (SCRAPED_IMAGES_BUCKET, filename_full),
            image_full_width=width,
            image_full_height=height,
            image_thumbnail_url='https://storage.googleapis.com/%s/%s' % (SCRAPED_IMAGES_BUCKET, filename_thumb),
            image_thumbnail_width=360,
            image_thumbnail_height=760,
            image_source_url=image_url,
            image_source_sha1=sha1
        ).save()
    except Exception as e:
        print("FAIL [%s] Unexpected issue saving to database [%s]" % (source_url, str(e)))
        return

    print("OK [%s] by [%s] saved [%s]" % (title, author, sha1))
