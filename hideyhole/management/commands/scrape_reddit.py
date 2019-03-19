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

import praw
import re
import os
import time

from django.core.management.base import BaseCommand

from hideyhole.util.wallpaper import save_scraped_wallpaper


class Command(BaseCommand):
    REQUEST_LIMIT = 1000

    # hardcoded for now
    CATEGORIES = [
        's10_cutout',  # shortest first
        's10e_cutout',
        's10plus_cutout',
        'amoleddark',
        'abstract',
        'anime',
        'artwork',
        'minimalistic',
        'nature',
        'person',
        'urban',
        'other'
    ]

    def category_from_title_or_flair(self, title_or_flair):
        if not title_or_flair:
            return None

        haystack = title_or_flair.lower().replace(" ", "").replace("+", "plus")
        for category in self.CATEGORIES:
            if category.replace("_", "") in haystack:
                return category

        # maybe s10 is mentioned without cutout
        for category in reversed([x.replace("_cutout", "") for x in self.CATEGORIES if x.endswith("_cutout")]):
            if category in haystack:
                return category + "_cutout"

        return None

    def remove_text_inside_brackets(self, text, brackets="()[]"):
        # from StackOverflow
        count = [0] * (len(brackets) // 2)  # count open/close brackets
        saved_chars = []
        for character in text:
            for i, b in enumerate(brackets):
                if character == b:  # found bracket
                    kind, is_close = divmod(i, 2)
                    count[kind] += (-1) ** is_close  # `+1`: open, `-1`: close
                    if count[kind] < 0:  # unbalanced bracket
                        count[kind] = 0  # keep it
                    else:  # found bracket to remove
                        break
            else:  # character is not a [balanced] bracket
                if not any(count):  # outside brackets
                    saved_chars.append(character)
        return ''.join(saved_chars)

    def sanitize_title(self, title):
        ret = self.remove_text_inside_brackets(title).strip().replace("  ", " ").replace(" plus", "plus").replace("+", "plus")

        for category in reversed([x.replace("_cutout", "") for x in self.CATEGORIES if x.endswith("_cutout")]):
            pattern = re.compile(re.escape(category), re.IGNORECASE)
            ret = pattern.sub("", ret)

        ret = ret.strip(" .,/-*").replace("  ", " ")
        if ret.lower().endswith(' for'):
            ret = ret[0:len(ret)-4]
        return ret

    def handle(self, *args, **options):
        # env's set by kubernetes with secrets
        reddit = praw.Reddit(client_id=os.getenv('REDDIT_ID'), client_secret=os.getenv('REDDIT_SECRET'), user_agent=os.getenv('REDDIT_USER_AGENT'))

        #TODO scrape comments for 'titled' links in first X threads from new
        #TODO scrape first X threads from hot as well, as popular mosts may see more new comments, and we get the stickies too
        for submission in reddit.subreddit('S10wallpapers').new(limit=self.REQUEST_LIMIT):
            time.sleep(0.1)  # we need more delay if we're going to do comments, due to Reddit API limits

            if submission.domain in ['i.redd.it', 'i.imgur.com', 'imgur.com']:
                category = self.category_from_title_or_flair(submission.link_flair_text) or self.category_from_title_or_flair(submission.title)
                if not category:
                    continue

                url = submission.url
                if 'imgur.com/a/' in submission.url:
                    # skip albums from imgur
                    continue
                elif '/imgur.com/' in submission.url:
                    # http(s)://imgur.com/xxxx(.jpg) --> https://i.imgur.com/xxxx.jpg
                    url = submission.url.replace('/imgur.com/', '/i.imgur.com/')
                    if not url.endswith('.jpg') and not url.endswith('.png'):
                        url += '.jpg'

                title = self.sanitize_title(submission.title)

                permalink = submission.permalink
                if 'reddit.com' not in permalink:
                    permalink = 'https://reddit.com' + permalink
                save_scraped_wallpaper(submission.author, title, category, submission.score, permalink, url, submission.created_utc)
