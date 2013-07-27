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

consolewait = timedelta(seconds=settings.CONSOLE_WAIT)
giveupwait = timedelta(seconds=600)
gaveup_msg = "_UNAVAILABLE_"

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--long', '-l', dest='long',
            help='Help for the long options'),
    )
    help = 'Poll to get console outputs'

    def handle(self, **options):
        conns = { }
        instances = Instances.objects.defer("console_end").filter(running_time__isnull=False, console_start="")
        #if len(instances):
        #    log.debug("found %i instances with empty console_start" %
        #        len(instances))
        for inst in instances:
            if not needsStartConsole(inst): continue
            r = str(inst.region)
            conns[r] = getConn(inst.region, conns.get(r))
            saveConsole(inst, "console_start", inst.running_time, conns[r])

        instances = Instances.objects.defer("console_start").filter(terminated_time__isnull=False, console_end="")
        #if len(instances):
        #    log.debug("found %i instances needing console_stop" %
        #        len(instances))
        for inst in instances:
            if not needsTermConsole(inst): continue
            r = str(inst.region)
            conns[r] = getConn(inst.region, conns.get(r))
            saveConsole(inst, "console_end", inst.terminated_time, conns[r])

def saveConsole(inst, update_fld, giveup_ref, conn=None):
    output=ec2_helper.get_console_output(inst,inst.region,conn)

    giveup = False
    if giveup_ref:
        giveup = (giveup_ref + giveupwait > util.dtnow())

    if not output and not giveup: return

    if not output:
        #log.warn("giving up on %s for %s" % (update_fld, inst))
        output = "%s: %s" % (gaveup_msg, util.dtnow())
    else:
        #log.info("saving %s for %s" % (update_fld,inst))
        pass

    inst = Instances.objects.get(pk=inst.pk)
    setattr(inst, update_fld, output)
    inst.save()

def needsStartConsole(instance):
    # an instance should have its console collected if
    # it doesn't yet have console_start
    if instance.console_start: return False

    # it is > pending state
    if instance.status() == "pending": return False

    # the instance could have gone "straight to terminated" or
    # for some other reason not have a running time
    if not instance.running_time: return False

    # it has been at least a pre-defined time since it was found running
    if instance.running_time + consolewait > util.dtnow(): return False

    return True

def needsTermConsole(instance):
    # an instance should have its terminating console collected if
    # it doesn't yet have console_end
    if instance.console_end: return False

    # it is terminated
    if instance.status() != "terminated": return False
    return True

def getConn(region,conn=None):
    if not conn:
        return(ec2_helper.ec2_connection(region))
    return conn

# vi: ts=4 expandtab
