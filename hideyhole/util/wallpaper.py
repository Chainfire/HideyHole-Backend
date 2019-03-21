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
import paramiko
from scp import SCPClient

from hideyhole.models import BannedUrl, Wallpaper


class KeyPolicy(paramiko.client.MissingHostKeyPolicy):
    def __init__(self):
        pass

    def missing_host_key(self, client, hostname, key):
        pass


class KeyWrapper():
    def __init__(self, data):
        self.data = data

    def readlines(self):
        return [x + '\n' for x in self.data.split(';')]


# this is only called from cron/shell scripts that should continue, hence the odd error handling
def save_scraped_wallpaper(author, title, category, popularity, source_url, image_url, added):
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

    source_png = False
    if im.mode == 'RGBA' or im.mode == 'LA' or im.mode == 'P' or image_url.endswith('.png'):
        source_png = True
    filename_full = 'images/' + sha1 + ('.png' if source_png else '.jpg')
    filename_thumb = 'thumbnails/' + sha1 + '.jpg'
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

        if thumb.mode == 'P':
            # convert Palette images to RGBA before converting to RGB
            thumb = thumb.convert("RGBA")

        if thumb.mode != 'RGB':
            # make sure we can save as jpeg
            thumb = thumb.convert("RGB")

        with io.BytesIO() as output:
            thumb.save(output, "JPEG", quality=80)
            image_thumb_bytes = output.getvalue()
    except:
        print("FAIL [%s] Thumbnail create fail" % source_url)
        return

    # our own storage server, env variables from secrets
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(KeyPolicy())
        pkey = paramiko.RSAKey.from_private_key(KeyWrapper(os.getenv("STORAGE_SSH_KEY")))
        ssh.connect(os.getenv("STORAGE_SSH_HOST"), username=os.getenv("STORAGE_SSH_USERNAME"), pkey=pkey, port=int(os.getenv("STORAGE_SSH_PORT")), timeout=30, allow_agent=False, look_for_keys=False, compress=False)

        scp = SCPClient(ssh.get_transport())
        scp.putfo(io.BytesIO(image_full_bytes), os.getenv("STORAGE_SSH_PATH") + filename_full)
        scp.putfo(io.BytesIO(image_thumb_bytes), os.getenv("STORAGE_SSH_PATH") + filename_thumb)
        scp.close()

        ssh.close()
    except Exception as e:
        print("FAIL [%s] Unexpected issue saving to storage server [%s]" % (source_url, str(e)))
        return

    # save
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
            image_full_url='https://hideyhole-images.chainfire.eu/%s' % filename_full,
            image_full_width=width,
            image_full_height=height,
            image_thumbnail_url='https://hideyhole-images.chainfire.eu/%s' % filename_thumb,
            image_thumbnail_width=360,
            image_thumbnail_height=760,
            image_source_url=image_url,
            image_source_sha1=sha1
        ).save()
    except Exception as e:
        print("FAIL [%s] Unexpected issue saving to database [%s]" % (source_url, str(e)))
        return

    print("OK [%s] by [%s] saved [%s]" % (title, author, sha1))
