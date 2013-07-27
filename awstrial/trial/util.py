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

import datetime
from dateutil.tz import tzutc
from dateutil import parser 
from StringIO import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import MIMEBase
import string
import random
import gzip

def dtnow():
	return(datetime.datetime.utcnow().replace(tzinfo=None))

def aws2datetime(awstime):
        return(parser.parse(awstime).replace(tzinfo=None))

CI_SCRIPT="text/x-shellscript"
CI_SCRIPT_START="#!"
CI_UPSTART="text/upstart-job"
CI_UPSTART_START="#upstart-job"
CI_BOOTHOOK="text/cloud-boothook"
CI_BOOTHOOK_START="#cloud-boothook"
CI_INCLUDE="text/x-include-url"
CI_INCLUDE_START="#include"
CI_CLOUDCONFIG="text/cloud-config"
CI_CLOUDCONFIG_START="#cloud-config"
CI_PARTHANDLER="text/part-handler"
CI_PARTHANDLER_START="#part-handler"

def rand_str(strlen=32, select_from=string.letters+string.digits):
    return("".join([random.choice(select_from) for x in range(0, strlen)]))

def rand_user_password(pwlen=9):
    selfrom=(string.letters.translate(None,'loLOI') +
             string.digits.translate(None,'01'))
    return(rand_str(pwlen,select_from=selfrom))

def guess_part_type(content):
    swith_map = {
        CI_INCLUDE_START : CI_INCLUDE,
        CI_SCRIPT_START : CI_SCRIPT,
        CI_CLOUDCONFIG_START : CI_CLOUDCONFIG,
        CI_UPSTART_START : CI_UPSTART,
        CI_PARTHANDLER_START : CI_PARTHANDLER,
        CI_BOOTHOOK_START : CI_BOOTHOOK,
    }
    for start,mtype in swith_map.items():
        if content.startswith(start):
            return(mtype)
    return(None)


# return a part item, that can then be fed as an item in a list
# to parts2mime
def partItem(part_content, part_type=None, filename=None):
    return((part_type,part_content,filename))

# plist expects to find a 
def parts2mime(plist, compress=True):
    count=0
    outer = MIMEMultipart()
    for item in plist:
        count=count+1
        (mtype,content,fname)=item
        if not mtype:
            mtype = guess_part_type(content)

        (maintype, subtype) = mtype.split('/', 1)
        if maintype == 'text':
            msg = MIMEText(content, _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(content)
            # Encode the payload using Base64
            encoders.encode_base64(msg)

        # Set the filename parameter
        if not fname:
            fname = 'mpart-%03d' % count

        msg.add_header('Content-Disposition', 'attachment',
            filename=fname)

        outer.attach(msg)

    if compress:
        ofile = StringIO()
        gfile = gzip.GzipFile(mode='wb',fileobj=ofile,filename="multipart-ud")
        gfile.write(outer.as_string())
        gfile.close()
        ofile.flush()
        return(ofile.getvalue())
    else:
        return(outer.as_string())

def find_config(config, configs):
    for c in configs:
        if c['name'] == config:
            return(c)
            break
    return None

# vi: ts=4 expandtab
