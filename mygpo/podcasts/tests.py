#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

import unittest
import uuid
from datetime import datetime, timedelta

from django.test import TestCase

from mygpo.podcasts.models import Podcast


def create_podcast(**kwargs):
    return Podcast.objects.create(id=uuid.uuid1().hex, **kwargs)


class PodcastTests(unittest.TestCase):
    """ Test podcasts and their properties """

    def test_next_update(self):
        """ Test calculation of Podcast.next_update """
        last_update = datetime(2014, 03, 31, 11, 00)
        update_interval = 123  # hours

        # create an "old" podcast with update-information
        create_podcast(last_update=last_update, update_interval=update_interval)

        # the podcast should be the next to be updated
        p = Podcast.objects.order_by_next_update().first()

        # assert that the next_update property is calculated correctly
        self.assertEqual(p.next_update,
                         last_update + timedelta(hours=update_interval))


    def test_get_or_create_for_url(self):
        """ Test that get_or_create_for_url returns existing Podcast """
        URL = 'http://example.com/get_or_create.rss'
        p1 = Podcast.objects.get_or_create_for_url(URL)
        p2 = Podcast.objects.get_or_create_for_url(URL)
        self.assertEqual(p1.pk, p2.pk)


class PodcastGroupTests(unittest.TestCase):
    """ Test grouping of podcasts """

    def test_group(self):
        self.podcast1 = create_podcast()
        self.podcast2 = create_podcast()

        group = self.podcast1.group_with(self.podcast2, 'My Group', 'p1', 'p2')

        self.assertIn(self.podcast1, group.podcast_set.all())
        self.assertIn(self.podcast2, group.podcast_set.all())
        self.assertEquals(len(group.podcast_set.all()), 2)
        self.assertEquals(group.title, 'My Group')
        self.assertEquals(self.podcast1.group_member_name, 'p1')
        self.assertEquals(self.podcast2.group_member_name, 'p2')

        # add to group
        self.podcast3 = create_podcast()

        group = self.podcast1.group_with(self.podcast3, 'My Group', 'p1', 'p3')

        self.assertIn(self.podcast3, group.podcast_set.all())
        self.assertEquals(self.podcast3.group_member_name, 'p3')

        # add group to podcast
        self.podcast4 = create_podcast()

        group = self.podcast4.group_with(self.podcast1, 'My Group', 'p4', 'p1')

        self.assertIn(self.podcast4, group.podcast_set.all())
        self.assertEquals(self.podcast4.group_member_name, 'p4')


def load_tests(loader, tests, ignore):
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastTests))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastGroupTests))
    return tests