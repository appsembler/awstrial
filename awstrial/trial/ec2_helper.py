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

from trial.models import Campaign, Instances
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

from django.conf import settings

from boto.ec2.connection import EC2Connection, RegionInfo
from boto import connect_ec2
import boto
import time
from trial import util

import yaml


def ec2_connection(region):
    a = 1
    if settings.ALTERNATE_CLOUD:
        # For testing against euca
        region = RegionInfo(
            name=settings.ALTERNATE_CLOUD['region'],
            endpoint=settings.ALTERNATE_CLOUD['endpoint']
        )

        connection = boto.ec2.EC2Connection(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=region,
            is_secure=settings.ALTERNATE_CLOUD['is_secure'],
            port=settings.ALTERNATE_CLOUD['port'],
            path=settings.ALTERNATE_CLOUD['endpoint_path']
        )

    else:

        reginfo = RegionInfo(name=region, endpoint='ec2.%s.amazonaws.com' % region)
        connection = boto.ec2.EC2Connection(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region = reginfo)

    return connection

def runit(campaign,lpid=None,regions=None,config=None, password=None):
    sec_key = util.rand_str(32)
    if regions is None:
        regions = [r for r in settings.REGIONS_TRY_ORDER
                         if settings.REGION2AMI.has_key(r)]
        regions = [r for r in settings.REGIONS_TRY_ORDER
                         if settings.REGION2AMI.has_key(r)]

    cust = { }
    cust['config'] = config
    cust['password'] = password

    parts=[]
    parts.append(
        util.partItem(
            render_to_string("import-launchpad-ssh-keys",
                { 'debug' : settings.DEBUG, 'launchpad_id' : lpid, 'password' : password } ),
            part_type=util.CI_SCRIPT, filename="10-launchpad-ssh-keys"))

    site = Site.objects.get(pk=settings.SITE_ID)
    callback_url = "%s/info_callback/%s" % (site.domain, sec_key)
    parts.append(
        util.partItem(
            render_to_string("info-callback",
                { 'debug' : settings.DEBUG, 'callback_url' : "%s/initial/" % callback_url } ),
            part_type=util.CI_SCRIPT, filename="99-info-callback"))

    parts.append(
        util.partItem(
            render_to_string("schedule-warnings",
                { 'debug' : settings.DEBUG, 'launch_time' : util.dtnow().strftime("%H:%M %Y-%m-%d UTC") } ),
            part_type=util.CI_SCRIPT, filename="50-schedule-warnings"))

    parts.append(
        util.partItem(
            render_to_string("log-login",
                { 'debug' : settings.DEBUG, 'callback_url' : "%s/login/" % callback_url }),
            part_type=util.CI_BOOTHOOK, filename="50-log-login"))

    parts.append(
        util.partItem(
            render_to_string("personal-hello", { 'debug' : settings.DEBUG, 'launchpad_id' : lpid }),
            part_type=util.CI_SCRIPT, filename="50-personal-hello"))

    parts.append(
        util.partItem(
            render_to_string("password-enable",
                { 'debug' : settings.DEBUG, 'user': 'ubuntu', 'password' : password }),
            part_type=util.CI_SCRIPT, filename="55-password-enable"))

    parts.append(
        util.partItem(
            render_to_string("byobu-countdown", { 'debug' : settings.DEBUG, }),
            part_type=util.CI_BOOTHOOK, filename="byobu-countdown"))
    cust['byobu']=True

    instcfg = None
    for c in settings.CONFIGS:
        if c['name'] == config:
            instcfg = c
            break
            
    if not instcfg:
        raise Exception("Invalid config %s" % config)

    if instcfg['template']:
        parts.append(
            util.partItem(
                render_to_string(instcfg['template'], { 'debug' : settings.DEBUG, }),
                part_type=util.CI_CLOUDCONFIG, filename=instcfg['template']))

    # Create the instance record in the database before creating it in ec2
    i = Instances.objects.create(instance_id='i-00000000',
                  campaign=Campaign.objects.get(name=campaign),
                  owner = User.objects.get(username=str(lpid)),
                  reservation_time=util.dtnow(),
                  secret=sec_key,
                  config_info=yaml.dump(cust))

    if True: #settings.DEBUG == False:

        region = None
        reservation = None
        ex = None
        
        try:
            for region in regions:
                if settings.ALTERNATE_CLOUD:
                    ami = settings.ALTERNATE_CLOUD['ami']
                else:
                    ami = settings.REGION2AMI[region]

                try:
                    ec2 = ec2_connection(region)

                    reservation = ec2.run_instances(ami,
                                   instance_type=settings.INSTANCE_TYPE,
                                   key_name=settings.INSTANCE_KEY_NAME,
                                   security_groups=settings.INSTANCE_SECURITY_GROUPS,
#                                   user_data=util.parts2mime(parts)
                                   )
                                   
                    break
                except boto.exception.EC2ResponseError as ex:
                    if ex.error_code == 'InstanceLimitExceeded': continue
                    if ex.error_code == 'InsufficientInstanceCapacity': continue
                    raise

            if reservation is None:
                raise ex

            instance = reservation.instances[0]
            i.instance_id=instance.id
            i.ami_id=ami
            i.region=region
            i.reservation_time=util.dtnow()
            i.save()
            #while not instance.update() == 'running': 
            #  time.sleep(5)
        except boto.exception.EC2ResponseError as ex:
            i.delete()
            raise ex
    else:
        i.ami = "ami-BADCOFFEE"
        i.instance = "i-406D088D"
        i.save()

# take an 'Instances' object, and a of a boto Instance
# and updates Instances object iff it has changed
def update_instance_from_aws(instance,aws_data):
    aws2inst = {
        'id' : 'instance_id',
        'launch_time' : 'reservation_time',
        'image_id' : 'ami_id',
        'ip_address' : 'ip',
        'public_dns_name' : 'hostname',
    }
    update = False
    for aattr,iattr in aws2inst.items():
        if aattr == "launch_time":
            aval = util.aws2datetime(getattr(aws_data,aattr,None))
        else:
            aval = getattr(aws_data,aattr,None)
        ival = getattr(instance,iattr,None)
        if aval and aval != ival:
            update = True
            setattr(instance,iattr,aval)
    state2datemap = {
        "pending" : "reservation_time",
        "running" : "running_time",
        "stopped" : "running_time",
        "shutting-down" : "shutdown_time",
        "terminated" : "terminated_time"
    }
    #print "state=%s" % aws_data.state
    for state,iattr in state2datemap.items():
        if ( aws_data.state == state and
             not getattr(instance,iattr,None) ):
            setattr(instance,iattr,util.dtnow())
            update = True
    return update

def update_instances(instances,region,conn=None):
    resultset = query_instances(instances, region, conn)
    aws_ihash = { }
    for res in resultset:
        for instance in res.instances:
            aws_ihash[instance.id]=instance

    #import sys; sys.stderr.write("%-15s: aws had %s, inst list had %s\n"
    #    % (region,len(aws_ihash), len(instances)))

    for inst in instances:
        # re-fetch the instance, in case it changed between
        # the original 'query_instances' and now.  It might have
        # changed if console_poll, or info_callback updated it (LP: #658362)
        inst = Instances.objects.get(instance_id=inst.instance_id,
                                     region=region)

        if inst.instance_id not in aws_ihash:
            # update the instance here also as it could be we lauched
            # then never updated until it was completely gone from the
            # aws side (hours later)
            inst.terminated_time = util.dtnow()
            import sys; sys.stderr.write("instance %s not seen in results, marking as terminated\n" % inst.instance_id)
            inst.save()
        elif update_instance_from_aws(inst,aws_ihash[inst.instance_id]):
            #import sys; sys.stderr.write("saving state of %s\n" % inst.instance_id)
            inst.save()

# return boto response for DescribeInstances of all instances
def query_instances(instances,region,conn=None):
    instanceList = []
    if not conn:
        conn = ec2_connection(region)
    for i in instances:
        instanceList.append(i.instance_id)
    return (conn.get_all_instances(instance_ids=instanceList))


def terminate_instances(instances,region,conn=None):
    """ Should reuse query_interface """
    if not len(instances):
        emp=()
        return emp

    if not conn:
        conn = ec2_connection(region)

    idlist = [ ]
    for i in instances: idlist.append(i.instance_id)

    return(conn.terminate_instances(idlist))

def get_console_output(instance,region,conn=None):
    if not conn:
        conn = ec2_connection(region)
    response=conn.get_console_output(instance.instance_id)
    if not response.output: return("")
    output = response.output.decode('utf-8','replace')
    return "%s\n%s\n" % (response.timestamp, output)

# vi: ts=4 expandtab
