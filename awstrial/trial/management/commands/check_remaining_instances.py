#    AWSTrial, A mechanism and service for offering a cloud image trial
#
#    Copyright (C) 2010  Scott Moser <smoser@ubuntu.com>
#    Copyright (C) 2010  Dave Walker (Daviey) <DaveWalker@ubuntu.com>
#    Copyright (C) 2010  Michael Hall <mhall119@gmail.com>
#    Copyright (C) 2010  Dustin Kirkland <kirkland@ubuntu.com>
#    Copyright (C) 2010  Andreas Hasenack <andreas@canonical.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.core.management.base import BaseCommand, CommandError

from trial.models import Campaign
import sys


def report(msgs):  
    # wrapper for print to reduce testing complexity
    if isinstance(msgs, list):
        for msg in msgs:
            print msg
    elif isinstance(msgs, basestring):
        print msg


def exit(level):  
    # wrapping sys.exit to reduce testing complexity
    sys.exit(level)


class Command(BaseCommand):
    help = 'checks the number of remaining instances for all active campaigns'
    ' warning at 10% remaining, critical at 5% remaining.'

    def handle(self, *args, **kwargs):
        campaigns = Campaign.objects.filter(active=True)
        if campaigns:
            msgs = []
            for campaign in campaigns:
                if campaign.remaining_level() == 0:
                    msgs.append('Critical: The campaign, %s, has none '
                                'of its instances remaining.' % campaign.name)
                elif campaign.remaining_level() <= 0.05:
                    msgs.append('Critical: The campaign, %s, has 5%% '
                                'or less of its instances remaining.'
                                % campaign.name)
                elif campaign.remaining_level() <= 0.1:
                    msgs.append('Warning: The campaign, %s, has 10%% or less '
                                'of its instances remaining.' % campaign.name)
                elif campaign.max_instances == 0:
                    msgs.append('Critical: The campaign, %s, '
                    'has max_instances set to 0. This is likely a '
                    'configuration error.' % campaign.name)
            if len(msgs) > 0:
                report(msgs)
                exit(1)
            else:
                exit(0)
        else:
            report('There are currently no active campaigns.')
            exit(1)
