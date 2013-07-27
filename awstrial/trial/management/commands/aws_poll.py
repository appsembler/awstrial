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

from trial.models import Instances
from trial import ec2_helper
from trial import util
from django.conf import settings
from datetime import timedelta

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--long', '-l', dest='long',
            help='Help for the long options'),
    )
    help = 'Poll to check the status'



##### Some of this logic should be moved to ec2_helper IMO

    def handle(self, **options):
        instPerReg = { }
        for region in settings.REGION2AMI.keys():
            instances = Instances.objects.filter(terminated_time=None, region=region)
            #print "have %s instances in %s" % (len(instances),region)
            ec2_helper.update_instances(instances,region)
            instPerReg[region]=instances

        lifespan = timedelta(seconds=settings.LIFETIME)
        for region,instances in instPerReg.iteritems():
            dt = util.dtnow()
            tokill = [ ]
            for inst in instances:
                # ignore anything not 'running'
                if inst.status() != 'running': continue

                if inst.olderThan(lifespan, dt):
                    tokill.append(inst)

            if len(tokill):
                #import sys; sys.stderr.write(
                #    "killing in %s: %s\n" % (region,tokill))
                ec2_helper.terminate_instances(tokill,region)

# vi: ts=4 expandtab
