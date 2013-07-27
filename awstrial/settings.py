import os
import sys

try:
    import ubuntu_website
    uw_import = True
except ImportError:
    print "You need the ubuntu_website theme"
    uw_import = False


PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))


DEBUG = False
TEMPLATE_DEBUG = DEBUG
STATIC_SERVE = DEBUG


ADMINS = (
    ('ISD Support', 'isd-support@canonical.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'awstrial.db'             # Or path to database file if using sqlite3.

DEFAULT_SITE_DOMAIN = 'domain.com'
DEFAULT_SITE_NAME = 'Sitename'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '!=xjt)_6e%s^3v9#wb@1%$67quslp2%cnih9g7v24movrl0lup'

# List of callables that know how to import templates from various sources.
if DEBUG:
    TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',      
    ]
else:
    TEMPLATE_LOADERS = [
        ('django.template.loaders.cached.Loader',(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    ]



TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
    "trial.context_processors.google_analytics_id",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = (
#   'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.github',
    # 'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.linkedin',
    # 'allauth.socialaccount.providers.twitter',
)


ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
    os.path.join(PROJECT_PATH, 'templates/cloud-init'),
)

if uw_import:
    TEMPLATE_CONTEXT_PROCESSORS += (
        "ubuntu_website.media_processor",
        "ubuntu_website.popup_check",
    )
    TEMPLATE_DIRS += (
        ubuntu_website.TEMPLATE_DIR,
    )



INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'adminaudit',
    # 'django_openid_auth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'trial',
    'south',
    #'pgtools',
)

AUTH_PROFILE_MODULE = 'trial.UserProfile'

# OPENID_CREATE_USERS = True
# OPENID_UPDATE_DETAILS_FROM_SREG = True
# LOGIN_URL = '/openid/login/'
# LOGIN_REDIRECT_URL = '/'
# OPENID_SSO_SERVER_URL = 'https://login.ubuntu.com/'
#OPENID_USE_AS_ADMIN_LOGIN = True

# from http://uec-images.ubuntu.com/query/maverick/server/daily.current.txt

## ami ids for Maverick RC (2010928.4) i386 ebs and instance store
ALTERNATE_CLOUD = False
default_ami_ids = { }

# Maverick EBS
# default_ami_ids['ebs'] = {
#   'ap-southeast-1' : 'ami-50c18602',
#   'eu-west-1' : 'ami-b5043fc1',
#   'us-east-1' : 'ami-605f8409',
#   'us-west-1' : 'ami-f5441fb0',
# }

# 12.04 precise amd64 EBS store
default_ami_ids['ebs'] = {
  'ap-northeast-1' : 'ami-51129850',
  'ap-southeast-1' : 'ami-a02f66f2',
  'ap-southeast-2' : 'ami-974ddead',
  'sa-east-1' : 'ami-5c7edb41',
  'eu-west-1' : 'ami-89b1a3fd',
  'us-east-1' : 'ami-23d9a94a',
  'us-west-1' : 'ami-c4072e81',
  'us-west-2' : 'ami-fb68f8cb',
}

# Maverick instance store
# default_ami_ids['instance'] = {
#   'ap-southeast-1' : 'ami-88ca8dda',
#   'eu-west-1' : 'ami-25e8d351',
#   'us-east-1' : 'ami-b89842d1',
#   'us-west-1' : 'ami-d5712a90',
# }

# 12.04 precise amd64 instance store
default_ami_ids['instance'] = {
  'ap-northeast-1' : 'ami-7d1d977c',
  'ap-southeast-1' : 'ami-b02f66e2',
  'ap-southeast-2' : 'ami-934ddea9',
  'sa-east-1' : 'ami-027edb1f',
  'eu-west-1' : 'ami-57b0a223',
  'us-east-1' : 'ami-d9d6a6b0',
  'us-west-1' : 'ami-72072e37',
  'us-west-2' : 'ami-5168f861',
}

REGION2AMI=default_ami_ids['instance']

# when launching an instance, this is the order in which regions will be
# tried if a region is not specified
REGIONS_TRY_ORDER = ( 'us-east-1', 'us-west-1', 'eu-west-1', 'ap-southeast-1' )

# instance_type: the type of instance to launch
# Note, t1.micro can only be run on EBS store instances.
INSTANCE_TYPE="m1.small"
# if set to a true value, instance_key_name must exist in each region
# (euca-describe-keypairs).  it is not required to be set.
INSTANCE_KEY_NAME=""
# security_groups must exist in each region (euca-describe-groups)
INSTANCE_SECURITY_GROUPS=("awstrial",)

LIFETIME = 60 * 55;
# wait this long after reservation start before bothering with console
CONSOLE_WAIT = 240;

BASE_URL = "http://example.com"

CONFIGS = [
    { 'name': 'default', 'description': 'Ubuntu Server (12.04 LTS) Base Install',
      'template': None, 'info_tmpl': 'cc-base-info' },
    { 'name': 'wordpress', 'description': 'Ubuntu Server (12.04 LTS) with WordPress',
      'template': 'cc-wordpress', 'info_tmpl': 'cc-wordpress-info' },
    { 'name': 'moinmoin', 'description': 'Ubuntu Server (12.04 LTS) with MoinMoin Wiki',
       'template': 'cc-moinmoin', 'info_tmpl': 'cc-moinmoin-info' },
    { 'name': 'drupal', 'description': 'Ubuntu Server (12.04 LTS) with Drupal 7',
       'template': 'cc-drupal', 'info_tmpl': 'cc-drupal-info' },
]


USER_BLOCK_EMAIL_BLACKLIST = True
USER_BLOCK_TOR_GATEWAY = True

# For site statistics
#GOOGLE_ANALYTICS_ID = 'UA-1018242-32'

LOG_PATH = None
import logging
try:
  from local_settings import *
except ImportError:
  logging.warning("No local_settings.py were found. See INSTALL for instructions.")

# configure logging
if LOG_PATH is None:
    LOG_PATH = '/tmp/awstrial.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple_formatter': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'log_to_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'simple_formatter',
            'filename': LOG_PATH,
        },
    },
    'loggers': {
        'root': {
            'handlers': ['log_to_file'], # specify what handler to associate
            'level': 'INFO',                 # specify the logging level
        },     
    }       
}

is_interactive = ('manage.py' in sys.argv[0]) if sys.argv else False
if is_interactive:
    # disable logging since we're using the ./manage.py from the shell
    # in order to prevent permission problems when multiple users
    # access the same log
    LOGGING_CONFIG = None

# vi: ts=4 expandtab
