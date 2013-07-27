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

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from trial.models import Campaign
import sys

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--long', '-l', dest='long',
            help='Help for the long options'),
    )
    help = 'add a campaign. <name> <verbose_name> <number> <active>'

    def handle(self, *args, **options):
        active = True
        if len(args) == 3:
            (name,vname,number) = args
        elif len(args) == 4:
            (name,vname,number,active) = args
            if active in ("0", "False", "FALSE", "false"):
                active = False
            else:
                active = True
        else:
            print "%s\n  bad usage" % self.help
            sys.exit(1)

        ncampaign = Campaign(active=active, name=name,
            verbose_name=vname, max_instances=number)
        ncampaign.save()

        print "created %s with %s. active=%s" % (name, number, active)

# vi: ts=4 expandtab
