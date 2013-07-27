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

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from trial import util
import yaml
import re
import logging


log = logging.getLogger('root') #using getLogger('root') here as logging to __name__ is not working


INSTANCE_STATUS = (
    ('reserved', _('reserved')),
    ('running', _('running')),
    ('shutdown', _('shutdown')),
)
EC2_REGIONS = (
    ('us-east-1', _('us-east-1')),
    ('us-west-1', _('us-west-1')),
    ('eu-west-1', _('eu-west-1')),
    ('ap-southeast-1', _('ap-southeast-1')),
)


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    opt_marketing = models.BooleanField()
    has_ssh = models.BooleanField()
    initial_ip = models.IPAddressField(null=True)
    
    def __unicode__(self):
        return self.user.username
   
    def can_start_trial(self, campaign):
        gmail_user = GmailAlias.registered_gmail_alias(self.user.email)
        if gmail_user: 
            user = gmail_user
        else:
            user = self.user
        if not Instances.objects.filter(campaign__name=campaign, owner=user): 
            return True

        # user is being denied a second trial
        if gmail_user and self.user != gmail_user:
            log.info("Trial denied to email %s: it appears to be an alias for the existing user %s" % (self.user.email, user.email))
        else:
            log.info("Second trial denied to email %s" % self.user.email)
        return False
    
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)


class EmailBlacklist(models.Model):
  domain = models.CharField(max_length=150, verbose_name=_('Domain of blacklisted domain'))

  def __unicode__(self):
      return self.domain

class Campaign(models.Model):
    verbose_name = models.CharField(max_length=150, verbose_name=_('Name of the Campaign'))
    name = models.CharField(max_length=150, verbose_name=_('The slug, to use in the URL'))
    verbose_name = models.CharField(max_length=150, verbose_name=_('Name of the Campaign'))
    max_instances = models.IntegerField(verbose_name=_('Number of instances authorised'))
    active = models.BooleanField(verbose_name=_('Is this Campaign active?'))
    def __unicode__(self):
        return self.verbose_name
    def remaining(self):
        instance_count = Instances.objects.filter(campaign__verbose_name=self.verbose_name).count()
        remaining = self.max_instances-instance_count
        return remaining
    def remaining_level(self):
        if self.max_instances > 0:
            return self.remaining() / float(self.max_instances)
        else:
            return 0


class Instances(models.Model):
    instance_id = models.SlugField(_("Instance Identifier"), max_length=10, null=False, db_index=True)
    campaign = models.ForeignKey(Campaign)
    owner = models.ForeignKey(User)
    # for each of the time fields, the general flow is expected to be:
    #   pending -> running -> shutting-down -> terminated
    # if a state is found, and the previous state's time is not recorded
    # the update code will set them the same
    #   ie, if a instance is terminated, but there is no shutting down_time yet
    #   then set it to same as terminated
    reservation_time = models.DateTimeField(help_text=_('Time the instance was requested'), verbose_name=_('Spawn'))
    running_time = models.DateTimeField(help_text=_('First time the instance was found to be in running or later state'), verbose_name=_('Run time'), blank=True, null=True)
    shutdown_time = models.DateTimeField(help_text=_('First time the instance was found shutting-down or terminated'), verbose_name=_('Shutting-down time'), blank=True, null=True)
    terminated_time = models.DateTimeField(help_text=_('Time the instance was found terminated'), verbose_name=_('Terminated time'), blank=True, null=True)
    ph_time = models.DateTimeField(verbose_name=_('Info Callback Time'), help_text=_('Time when instance called back with info (ie "Phoned Home")'), blank=True, null=True)
    region = models.CharField(verbose_name=_('EC2 Region'), max_length=16, null=True, choices=EC2_REGIONS)
    ami_id = models.SlugField(_("AMI Identifier"), max_length=12, null=True, db_index=False)
    console_start = models.TextField(verbose_name=_('Console Output at start'), blank=True, null=True)
    console_end = models.TextField(verbose_name=_('Console Output after terminated'), blank=True, null=True)
    hostname = models.CharField(verbose_name=_('EC2 Hostname'), max_length=128, blank=True)
    ip = models.CharField(verbose_name=_('IP address'), max_length=16, blank=True)
    pubkeys = models.TextField(verbose_name=_('instance public ssh keys'), blank=True, null=True)
    secret = models.CharField(help_text=_('This is a randomly generated secret shared between instance and server.  Should be one-time use only'), verbose_name=_('Secret Key'), max_length=32, blank=True)
    config_info = models.TextField(verbose_name=_('Configuration info'), blank=True, null=True)

    def __unicode__(self):
        return self.instance_id

    def status(self):
        # return the state based on the timestamps that are set
        # one of 'running', 'shutting-down'
        if self.terminated_time: return('terminated')
        if self.shutdown_time: return('shutting-down')
        if self.running_time: return('running')
        if self.reservation_time: return('pending')

    def olderThan(self, td, dt=None):
        # expects a time delta
        if not dt:
            dt = util.dtnow()
        return(self.reservation_time + td < dt)

    def _cfgval_get(self,name,default=None):
        if not self.config_info: self.config_info = ""
        c = yaml.load(self.config_info)
        if not isinstance(c,dict): c = { }
        if name in c: return c[name]
        return default

    def _cfgval_set(self,name,value):
        if not self.config_info: self.config_info = ""
        c = yaml.load(self.config_info)
        if not isinstance(c,dict): c = { }
        c[name]=value
        self.config_info = yaml.dump(c)

    @property
    def byobu(self):
        return(self._cfgval_get("byobu",False))

    @byobu.setter
    def byobu(self,val):
        self._cfgval_set("byobu",val)

    @property
    def password(self):
        return(self._cfgval_get("password",None))

    @password.setter
    def password(self,val):
        self._cfgval_set("password",val)

    @property
    def config(self):
        return(self._cfgval_get("config",None))

    @config.setter
    def config(self,val):
        self._cfgval_set("config",val)

    @property
    def remote_ips(self):
        return(self._cfgval_get("remote_ips",[]))

    @remote_ips.setter
    def remote_ips(self,val):
        self._cfgval_set("remote_ips",val)

    @property
    def testdata(self):
        return(self._cfgval_get("testdata",None))

    @testdata.setter
    def testdata(self,val):
        self._cfgval_set("testdata",val)


class Feedback(models.Model):
    user = models.ForeignKey(User)
    comment = models.TextField(verbose_name=_('Comments'))

    def __unicode__(self):
        return str(self.user)

class GmailAlias(models.Model):
    user = models.ForeignKey(User, unique=True, null=True)
    default_user = models.CharField(max_length=150, verbose_name=_('default user name of gmail account'))

    def __unicode__(self):
        return self.default_user
    
    @classmethod 
    def save_gmail_alias(cls, email, user):
        if cls.is_gmail_address(email):
            default_user = cls.clean_gmail_user(email)
            cls.objects.get_or_create(default_user=default_user, user=user)

    @staticmethod
    def clean_gmail_user(email):
        (user, domain) = email.split('@')
        u = user.replace('.', '')
        clean_user  = re.sub('\+.*', '', u)
        return clean_user

    @classmethod
    def registered_gmail_alias(cls, email):
        if email != u'':
            if cls.is_gmail_address(email):
                default_user = cls.clean_gmail_user(email)
                alias = cls.objects.filter(default_user=default_user)
                if alias:
                    return alias[0].user 
        return None 

    @staticmethod
    def is_gmail_address(email):
        (user, domain) = email.split('@')
        if domain == 'gmail.com':
            return True
        return False
