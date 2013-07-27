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

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext, Context
from django import forms
from django.forms.widgets import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404

from trial.models import Campaign, Instances, Feedback, GmailAlias
from trial.forms import FeedbackForm

#from trial import lp_helper

from trial import ec2_helper, util
from trial.auth import safe_user_required
from django.conf import settings


def index(request):
    """ Main landing Page """
    campaign = Campaign.objects.filter(active=True)

    context = {
            'campaign': campaign,
    }

    return render_to_response("index.html", context,
                              context_instance=RequestContext(request))

@login_required
@safe_user_required
def start(request,campaign):
    """ Check the auth'd user has an ssh key """
    profile = request.user.get_profile()
    # profile.has_ssh = lp_helper.has_sshkey(request.user)
    profile.save()
    
    GmailAlias.save_gmail_alias(profile.user.email, profile.user)
    return HttpResponseRedirect("/%s/run/" % campaign)

@login_required
@safe_user_required
@csrf_protect
def run_instance(request,campaign):
    current_campaign=Campaign.objects.get(name=campaign)
    profile = request.user.get_profile()
    # First, check they haven't already used their instance.
    if profile.can_start_trial(campaign):
        # Now Check the campaign is running and has avaliability left.
        if current_campaign.remaining() and (current_campaign.active):
            if request.method == "POST":
                # opt_marketing = opt in for marketing mail, bool
                user = request.user.get_profile()
                user.opt_marketing = request.POST.get('opt_marketing', '')
                user.save()

                # a = disclaimer box
                a = request.POST.get('a', '')
                if a:
                    #try:
                    region = request.POST.get('region',None)
                    if region is not None:
                        regions = ( region, )
                    else:
                        regions = settings.REGIONS_TRY_ORDER
                    config = request.POST.get('config', '')
                    set_password = request.POST.get('set_password',None)

                    password=None
                    if set_password:
                        password=util.rand_user_password()

                    ec2_helper.runit(campaign,lpid=request.user, regions=regions, config=config, password=password)
                    #send_mail(subject, message, from_email, ['davewalker@ubuntu.com'])
                    #except BadHeaderError:   #Example of basic error handling
                    #	return HttpResponse('Invalid header found.')
                    return HttpResponseRedirect("/%s/instance_info/" % campaign)

            # if the user did not have ssh keys, then the contacts.html
            # form will set a hidden form field indicating to set a password
            set_password = False
            if not request.user.get_profile().has_ssh:
                set_password = True

            return render_to_response('contacts.html',
                { 'form': Instances(), 'settings': settings,
                  'set_password': set_password },
                context_instance=RequestContext(request))

        else:
            return HttpResponseRedirect("/") # redirect to main page, campaign exceeded.
	
    #return render_to_response('contacts.html', {'form': Instances()},
    #			RequestContext(request))
    return HttpResponseRedirect("/%s/instance_info/" % campaign)

@login_required
@safe_user_required
def reserved_instance(request,campaign):
    """ Instance is now reserved """
    return render_to_response('thankyou.html', RequestContext(request))

@login_required
@safe_user_required
def info_instance(request,campaign):
    """ Return details about Instance """
    instances = Instances.objects.filter(owner=request.user, campaign__name=campaign)
    if not instances: 
        return HttpResponseRedirect("/account-problem/")
    instcfg = util.find_config(instances[0].config,settings.CONFIGS)
    context = {
        'instance': instances[0],
        'config': instcfg,
        'debug': settings.DEBUG,
    }
    context['cloudconfig']=None
    if instcfg and instcfg['template']:
        context['cloudconfig']=render_to_string(instcfg['template'], { })

    return render_to_response('instance.html', context,
                              context_instance=RequestContext(request))

@login_required
@safe_user_required
def feedback(request):
    theUser = request.user
    try:
        instance = Feedback.objects.get(user=theUser)
    except Feedback.DoesNotExist:
        instance = Feedback(user=theUser)
    if request.method == 'POST': # If the form has been submitted...
        form = FeedbackForm(request.POST, instance = instance) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            form.save()
            return render_to_response('thankyou.html',
                context_instance=RequestContext(request))
    else:
        form = FeedbackForm(instance = instance) # An unbound form

    templates = { 'form': form, 'user': request.user }
    return render_to_response('feedback.html', templates,
                              context_instance=RequestContext(request))

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')

# vi: ts=4 expandtab
