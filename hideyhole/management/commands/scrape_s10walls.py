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

import datetime
import requests
import html

from django.core.management.base import BaseCommand

from hideyhole.util.wallpaper import save_scraped_wallpaper


class Command(BaseCommand):
    def handle(self, *args, **options):
        for url, category in [("https://www.galaxys10wallpapers.com/category/s10/page/%d/", "s10_cutout"),
                              ("https://www.galaxys10wallpapers.com/category/s10-plus/page/%d/", "s10plus_cutout")]:

            date_last = datetime.datetime(2019, 1, 1, 0, 0, 0, 0, datetime.timezone.utc).timestamp()

            page = 1
            while True:
                r = requests.get(url % page)
                if r.status_code != 200:
                    break

                data = r.text
                while '<div class="post-content ' in data:
                    data = data[data.find('<div class="post-content ') + 1:]

                    next = data.find('<div class="post-content ')
                    if next > 0:
                        current = data[0:next]
                    else:
                        current = data

                    link = False
                    if 'srcset="' in current:
                        current = current[current.find('srcset="') + 8:]
                        link = current[0:current.find('"')]
                        link = [x for x in link.split(' ') if x.startswith('http')][-1]

                    author = False
                    title = False

                    if '"bookmark">' in current:
                        href = current[0:current.find('"bookmark">')]
                        href = href[href.rfind('href="') + 6:]
                        href = href[0:href.find('"')]

                        title = current[current.find('"bookmark">') + 11:]
                        title = title[0:title.find('<')]
                        if ' by ' in title:
                            author = title[title.find(' by ') + 4:]
                            title = title[0:title.find(' by ')]
                        else:
                            author = 'Unknown'

                        if '[' in title:
                            title = title[0:title.find('[')].strip()
                        if '[' in author:
                            author = author[0:author.find('[')].strip()

                    if author and title and link:
                        author = html.unescape(author)
                        title = html.unescape(title)

                        save_scraped_wallpaper(author, title, category, 0, href, link, date_last)
                        date_last -= 1

                page += 1
