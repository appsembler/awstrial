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

from trial.models import Campaign, Instances, Feedback
from trial import ec2_helper, lp_helper, util
from django.conf import settings
from django.http import HttpResponse

def errmsg(msg):
    if settings.DEBUG:
        return("failed to register: %s\n" % msg)
    return("failed to register")


def handle_login(request, inst):
    remote_ip = request.POST.get('remote-ip','')
    if len(inst.remote_ips) > 20:
        # 20 unique IPs login?  I should log this or something
        # raise Exception("%s had %i logins" % (inst,len(inst.remote_ips)))
        pass
    else:
        ipl = inst.remote_ips
        if remote_ip not in map(lambda e: e[0], ipl):
            # simply doing inst.remote_ips.append() doesn't seem
            # to take, so do the copy to ipl then assign to inst.remote_ips
            ipl.append((remote_ip,util.dtnow()))
            inst.remote_ips = ipl
            inst.save()

    return(HttpResponse("logged login of %s\n" % remote_ip))

def handle_initial(request, inst):
    # if this instance is already registered
    if inst.pubkeys:
        return HttpResponse(errmsg("pubkeys already stored for %s" % inst.instance_id))
    
    if inst.ph_time:
        return HttpResponse(errmsg("you only get one call home"))
    
    pubkeys = request.POST.get('pubkeys','')

    inst.pubkeys = pubkeys
    inst.ph_time = util.dtnow()
    
    if settings.DEBUG and 'testdata' in request.POST:
        inst.testdata = request.POST.get('testdata', '')
    inst.save()
    return(HttpResponse("registered keys %s\n" % inst.instance_id))

modes = { 'initial' : handle_initial, 'login' : handle_login }

def info_callback(request,secret, mode):
    iid = request.POST.get('instance-id','')

    if mode not in modes:
        return HttpResponse(errmsg("invalid mode %s" % mode))

    if not iid:
        return HttpResponse(errmsg("iid not given"))

    res = Instances.objects.filter(instance_id=iid)

    # TODO: django doc indicates that len() on a QuerySet is
    # possibly bad.  but I dont think it necessarily is here
    if len(res) > 1:
        # uh-oh.  (this is actually possible, 
        # region/instance-id should be unique, but could have
        # duplicate instance-ids across regions
        return HttpResponse(errmsg("multiple matching instances: %s" % iid))

    # since there is only one item, this just gets it
    inst = None
    for inst in res: pass

    if not inst:
        return HttpResponse(errmsg("iid %s not found" % iid))

    # if the secret key doesn't match
    if secret != inst.secret:
        return HttpResponse(errmsg("invalid secret"))
    
    return(modes[mode](request,inst))

# vi: ts=4 expandtab
