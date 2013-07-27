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

from django.http import HttpResponseRedirect
from trial.models import EmailBlacklist
from django.conf import settings

import DNS
import socket
import logging


def blacklisted_email_domain(email):
    """ Return true if the domain portion of the email address is blocked """
    # only proceed if the blacklist is enabled
    if settings.USER_BLOCK_EMAIL_BLACKLIST:
        if email != u'':
            (user, domain) = email.split('@')
            domains = [domain]

            # now check if the domain is in the form of abc.something.com
            domain_parts = domain.split('.')
            while len(domain_parts) > 2:
                # we have a greater 2nd level domain, check if 2nd level is blocked
                domains.append('.'.join(domain_parts[1:]))
                domain_parts.pop(0)

            if EmailBlacklist.objects.filter(domain__in=domains):
                logger = logging.getLogger('root')
                logger.info("User's email matches a blacklisted domain: %s"
                % domain)
                return True
    return False

def client_using_tor(request):
    if settings.USER_BLOCK_TOR_GATEWAY:

        DNS.ParseResolvConf()

        remote_addr = request.META['REMOTE_ADDR']
        client = ".".join(reversed(remote_addr.strip().split('.')))

        TARGET = ".".join(reversed(socket.gethostbyname(request.META['SERVER_NAME']).strip().split('.')))
        PORT = "443"
        TOR_SUBDOMAIN = "ip-port.exitlist.torproject.org"

        lookup = ("%s.%s.%s.%s") % (client,PORT,TARGET,TOR_SUBDOMAIN)
        request = DNS.DnsRequest(name=lookup,qtype='A')
        answer=request.req()

        if answer.header['status'] == "NOERROR":
            logger = logging.getLogger('root')
            logger.info('Client %s is using TOR' % remote_addr)
            return True
    return False

def log_first_ip(request):
    if request.user.get_profile().initial_ip == None:
        profile = request.user.get_profile() 
        profile.initial_ip = request.META['REMOTE_ADDR']
        profile.save()

def safe_user_required(f):
        def wrap(request, *args, **kwargs):
                log_first_ip(request)
                if blacklisted_email_domain(request.user.email):
                        return HttpResponseRedirect("/account-problem/")
                if client_using_tor(request):
                        return HttpResponseRedirect("/account-problem/")
                return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

