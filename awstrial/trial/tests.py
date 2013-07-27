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
from unittest import TestCase as UnitTestCase
from django.test import TestCase as DjangoTestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from mock import patch, Mock
from trial import ec2_helper
from trial.models import (
     Campaign,
     Instances,
     EmailBlacklist,
     GmailAlias,
     UserProfile,
)
from trial.auth import blacklisted_email_domain, client_using_tor
from trial.management.commands.check_remaining_instances import Command
from trial import export
import logging
import socket


def make_user(*args, **user_values):
    """A factory function to create users."""
    return _make_object(User, user_values, args,
        username='testuser',
        first_name='Test',
        last_name='User',
        email='test@example.org',
        date_joined=datetime.datetime.now())

def make_campaign(*args, **user_values):
    """A factory function to create campaigns."""
    return _make_object(Campaign, user_values, args,
        name='test-campaign',
        verbose_name='Test Campaign',
        max_instances=5,
        active=True)

def make_instance(user, campaign, **user_values):
    """A factory function to create instances."""
    return _make_object(Instances, user_values, (),
        instance_id='instance_1',
        campaign=campaign,
        reservation_time=datetime.datetime.now(),
        running_time=datetime.datetime.now(),
        hostname='testing.localhost',
        ip='127.0.0.1',
        secret='12345678',
        owner=user)

def _make_object(klass, user_values, *args, **default_values):
    """Construct a database object.  Override the default values if requested.
    """
    if args[0]:
        raise RuntimeError("This function only takes keyword arguments "
                           "(got %r)" % args)
    default_values.update(user_values)
    return klass.objects.create(**default_values)


class TestExporter(DjangoTestCase):
    """
    Tests the export APIs
    """

    def setUp(self):
        self.create_date = datetime.datetime.now()
        self.user = User.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.org',
            date_joined=self.create_date
        )
        self.profile = self.user.get_profile()
        self.profile.opt_marketing = True
        self.profile.save()

        self.campaign = Campaign.objects.create(
            name='test-campaign',
            verbose_name='Test Campaign',
            max_instances=5,
            active=True,
        )

        self.instance = Instances.objects.create(
            instance_id='i-00000001',
            campaign=self.campaign,
            owner=self.user,
            reservation_time=self.create_date,
        )

    def test_full_export(self):
        users = export.get_marketing_opt_in_users()
        self.assertEquals(1, len(users))
        self.assertEquals(self.user.id, users[0]['id'])
        self.assertEquals(self.user.username, users[0]['username'])
        self.assertEquals(self.user.first_name, users[0]['first_name'])
        self.assertEquals(self.user.last_name, users[0]['last_name'])
        self.assertEquals(self.user.email, users[0]['email'])
        self.assertEquals(self.user.date_joined, users[0]['created'])

    def test_partial_export_prev(self):
        prev_day = self.create_date - datetime.timedelta(days=1)
        users = export.get_marketing_opt_in_users(created_after=prev_day)
        self.assertEquals(1, len(users))

    def test_partial_export_after(self):
        next_day = self.create_date + datetime.timedelta(days=1)
        users = export.get_marketing_opt_in_users(created_after=next_day)
        self.assertEquals(0, len(users))

    def test_opt_out(self):
        self.profile.opt_marketing = False
        self.profile.save()
        users = export.get_marketing_opt_in_users()
        self.assertEquals(0, len(users))

    def test_opt_in_after_user_joined(self):
        prev_day = self.create_date - datetime.timedelta(days=1)
        self.instance.reservation_time = prev_day
        self.instance.save()

        users = export.get_marketing_opt_in_users(
            created_after=self.create_date)
        self.assertEquals(0, len(users))

        next_day = self.create_date + datetime.timedelta(days=1)
        self.instance.reservation_time = next_day
        self.instance.save()

        users = export.get_marketing_opt_in_users(created_after=prev_day)
        self.assertEquals(1, len(users))

    def test_user_without_instance(self):
        prev_day = self.create_date - datetime.timedelta(days=1)
        self.instance.delete()
        self.profile.opt_marketing = False
        self.profile.save()

        users = export.get_marketing_opt_in_users(created_after=prev_day)
        self.assertEquals(0, len(users))

        users = export.get_marketing_opt_in_users()
        self.assertEquals(0, len(users))


class TestEc2Helper(UnitTestCase):
    """
    Tests the calls to functions in the ec2_helper module
    """
    def setUp(self):
        self.old_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self.old_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self.old_alternate_cloud = getattr(settings, 'ALTERNATE_CLOUD', None)
        settings.AWS_ACCESS_KEY_ID = 'TestAccessKey'
        settings.AWS_SECRET_ACCESS_KEY = 'TestSecretKey'

    def tearDown(self):
        settings.AWS_ACCESS_KEY_ID = self.old_access_key
        settings.AWS_SECRET_ACCESS_KEY = self.old_secret_key
        settings.ALTERNATE_CLOUD = self.old_alternate_cloud

    @patch('boto.ec2.EC2Connection')
    def test_regular_connection(self, mock_connection):
        """
        Checks calling ec2_connection to the Amazon EC2 cloud service
        """

        settings.ALTERNATE_CLOUD = None
        conn = ec2_helper.ec2_connection('test-region')
        args, kargs = mock_connection.call_args

        self.assertEquals('TestAccessKey', kargs['aws_access_key_id'])
        self.assertEquals('TestSecretKey', kargs['aws_secret_access_key'])
        self.assertEquals('test-region', kargs['region'].name)
        self.assertEquals('ec2.test-region.amazonaws.com',
                          kargs['region'].endpoint)

    @patch('boto.ec2.EC2Connection')
    def test_alternate_connection(self, mock_connection):
        """
        Checks calling ec2_connection for an alternate EC2 cloud service
        """

        settings.ALTERNATE_CLOUD = {
            'region': 'alternate-region',
            'ami': 'ami-00000001',
            'endpoint': 'awstrial.testing.com',
            'endpoint_path': '/services/awstrial',
            'port': 8773,
            'is_secure': False,
        }
        conn = ec2_helper.ec2_connection('us-east-1')
        args, kargs = mock_connection.call_args

        self.assertEquals('TestAccessKey', kargs['aws_access_key_id'])
        self.assertEquals('TestSecretKey', kargs['aws_secret_access_key'])
        self.assertEquals('alternate-region', kargs['region'].name)
        self.assertEquals('awstrial.testing.com', kargs['region'].endpoint)
        self.assertEquals('/services/awstrial', kargs['path'])
        self.assertEquals(8773, kargs['port'])
        self.assertEquals(False, kargs['is_secure'])


class RunInstancesTestCase(DjangoTestCase):
    """
    Tests the calls to functions in the ec2_helper module
    """
    def setUp(self):
        self.old_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self.old_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self.old_alternate_cloud = getattr(settings, 'ALTERNATE_CLOUD', None)
        self.old_site_id = getattr(settings, 'SITE_ID', None)
        settings.AWS_ACCESS_KEY_ID = 'TestAccessKey'
        settings.AWS_SECRET_ACCESS_KEY = 'TestSecretKey'
        settings.ALTERNATE_CLOUD = None

    def tearDown(self):
        settings.AWS_ACCESS_KEY_ID = self.old_access_key
        settings.AWS_SECRET_ACCESS_KEY = self.old_secret_key
        settings.ALTERNATE_CLOUD = self.old_alternate_cloud
        settings.SITE_ID = self.old_site_id

    def call_run_instance(self, campaign):
        post_data = {
            'config': 'default',
            'a': 1,
            'launchbtn': 'Launch',
        }
        return self.client.post('/%s/run/' % campaign.name, post_data)

    @patch('boto.ec2.EC2Connection')
    def test_uses_sites_framework(self, mock_connection):
        """
        Checks that the callback url is based off the Site.name for this
        configuration
        """

        newsite = Site.objects.create(
            domain='testing.awstrial.org',
            name='http://testing.awstrial.org:8000',
        )
        settings.SITE_ID = newsite.id
        self.call_count = 0

        class MockInstance(object):

            def __init__(self, instance_id):
                self.id = instance_id

        class MockReservation(object):

            def __init__(self, instance_ids):
                self.instances = [MockInstance(i) for i in instance_ids]

        campaign = Campaign.objects.create(
            name='test-campaign',
            verbose_name='Test Campaign',
            max_instances=5,
            active=True,
        )

        def mock_run_instances(conn, *args, **kwargs):
            self.call_count += 1
            self.assertTrue('user_data' in kwargs)

            import StringIO
            import gzip
            import email
            gzipped_mime_data = StringIO.StringIO()
            gzipped_mime_data.write(kwargs['user_data'])
            gzipped_mime_data.seek(0)
            gzipped_mime_file = gzip.GzipFile(
                fileobj=gzipped_mime_data,
                mode='r')
            mime_data = gzipped_mime_file.read()
            mime_msg = email.message_from_string(mime_data)
            self.assertTrue(mime_msg.is_multipart())

            for mime_part in mime_msg.get_payload():
                if mime_part.get_filename() == '99-info-callback':
                    self.assertTrue(
                    'http://testing.awstrial.org:8000/info_callback/'
                        in mime_part.get_payload())

            return MockReservation(['i-test-%s' % self.call_count])
        mock_return = mock_connection.return_value
        mock_return.run_instances.side_effect = mock_run_instances

        user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpasswd')
        self.client.login(username='testuser', password='testpasswd')

        response = self.call_run_instance(campaign)
        self.assertEquals(1, Instances.objects.all().count())
        instance = Instances.objects.all()[0]

    @patch('boto.ec2.EC2Connection')
    def test_disallow_multiple_instances(self, mock_connection):
        """
        Checks that a user can't create multiple isntances by making requests
        in quick succession and causing a race condition
        """

        settings.ALTERNATE_CLOUD = None
        self.call_count = 0

        class MockInstance(object):

            def __init__(self, instance_id):
                self.id = instance_id

        class MockReservation(object):

            def __init__(self, instance_ids):
                self.instances = [MockInstance(i) for i in instance_ids]

        campaign = Campaign.objects.create(
            name='test-campaign',
            verbose_name='Test Campaign',
            max_instances=5,
            active=True,
        )

        def mock_run_instances(conn, *args, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                # call again before returning to create the race condition
                response = self.call_run_instance(campaign)

                args, kargs = mock_connection.call_args
                self.assertEquals('TestAccessKey', kargs['aws_access_key_id'])
                self.assertEquals('TestSecretKey',
                    kargs['aws_secret_access_key'])

                return MockReservation(['i-test-one'])
            else:
                return MockReservation(['i-test-two'])
        mock_return = mock_connection.return_value
        mock_return.run_instances.side_effect = mock_run_instances

        user = User.objects.create_user('testuser',
            'test@example.com', 'testpasswd')
        self.client.login(username='testuser', password='testpasswd')

        response = self.call_run_instance(campaign)
        self.assertEquals(1, Instances.objects.all().count())

    @patch('boto.ec2.EC2Connection')
    def test_allow_multiple_instances_on_multiple_campaigns(
        self, mock_connection):
        """
        Checks that a user can create multiple instances as long as they are on
        different campaigns
        """

        settings.ALTERNATE_CLOUD = None
        self.call_count = 0

        class MockInstance(object):

            def __init__(self, instance_id):
                self.id = instance_id

        class MockReservation(object):

            def __init__(self, instance_ids):
                self.instances = [MockInstance(i) for i in instance_ids]

        def mock_run_instances(conn, *args, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                return MockReservation(['i-test-one'])
            else:
                return MockReservation(['i-test-two'])
        mock_return = mock_connection.return_value
        mock_return.run_instances.side_effect = mock_run_instances

        campaign1 = Campaign.objects.create(
            name='test-campaign-1',
            verbose_name='Test Campaign 1',
            max_instances=5,
            active=True,
        )
        campaign2 = Campaign.objects.create(
            name='test-campaign-2',
            verbose_name='Test Campaign-2',
            max_instances=5,
            active=False,
        )

        user = User.objects.create_user('testuser',
            'test@example.com', 'testpasswd')
        self.client.login(username='testuser', password='testpasswd')

        response = self.call_run_instance(campaign1)
        self.assertRedirects(response, '/test-campaign-1/instance_info/')
        response = self.client.get('/test-campaign-1/instance_info/')
        self.assertEquals(200, response.status_code)
        self.assertEquals(1, Instances.objects.all().count())

        campaign1.active = False
        campaign1.save()

        campaign2.active = True
        campaign2.save()

        response = self.call_run_instance(campaign2)
        self.assertRedirects(response, '/test-campaign-2/instance_info/')
        response = self.client.get('/test-campaign-2/instance_info/')
        self.assertEquals(200, response.status_code)
        self.assertEquals(2, Instances.objects.all().count())


class TestDataTestCase(DjangoTestCase):
    """
    Tests the calls to functions in the ec2_helper module
    """
    def setUp(self):
        settings.DEBUG = True
        self.campaign = Campaign.objects.create(
            name='test-campaign',
            verbose_name='Test Campaign',
            max_instances=5,
            active=True,
        )

        self.user = User.objects.create_user('testuser',
            'test@example.com', 'testpasswd')
        self.client.login(username='testuser', password='testpasswd')

    def tearDown(self):
        settings.DEBUG = False

    def test_info_callback(self):
        """
        Checks that testdata passed to the info callback will be stored
        """
        instance = Instances.objects.create(
            instance_id='i-00000001',
            campaign=self.campaign,
            owner=self.user,
            reservation_time=datetime.datetime.now(),
            running_time=datetime.datetime.now(),
            hostname='testing.localhost',
            ip='127.0.0.1',
            secret='12345678',
        )
        pdata = {
            'instance-id': 'i-00000001',
            'pubkeys': 'TSA: 12345678',
            'testdata': 'Sample Test Data\n',
        }
        response = self.client.post('/info_callback/12345678/initial/', pdata)
        self.assertContains(response, 'registered keys')

        instance = Instances.objects.get(instance_id='i-00000001')
        self.assertEquals('Sample Test Data\n', instance.testdata)

    def test_display_in_instance_info(self):
        """
        Checks that an Instance's testdata is displayed on /instance_info/
        """

        instance = Instances.objects.create(
            instance_id='i-00000001',
            campaign=self.campaign,
            owner=self.user,
            reservation_time=datetime.datetime.now(),
            running_time=datetime.datetime.now(),
            ph_time=datetime.datetime.now(),
            hostname='testing.localhost',
            ip='127.0.0.1',
            pubkeys='TSA: 1234567890',
            secret='12345678',
        )
        instance.testdata = "Sample Test Data\n"
        instance.save()

        response = self.client.get('/test-campaign/instance_info/')
        self.assertContains(response, '<p>Test Data:</p>')
        self.assertContains(response, '<pre>Sample Test Data\n</pre>')


class MockRequest:

    def __init__(self, method='GET'):
        self.META = {'QUERY_STRING': ''}
        self.GET = {}
        self.POST = {}
        self.REQUEST = {}
        self.method = method
        self.environ = self.META


class LogHandlerTestCase(DjangoTestCase):
    """A mixin that adds a memento loghandler for testing logging."""

    class MementoHandler(logging.Handler):
        """A handler class which stores logging records in a list.
        From http://nessita.pastebin.com/mgc85uQT
        """

        def __init__(self, *args, **kwargs):
            """Create the instance, and add a records attribute."""
            logging.Handler.__init__(self, *args, **kwargs)
            self.records = []

        def emit(self, record):
            """Just add the record to self.records."""
            self.records.append(record)

        def check(self, level, msg, with_exc_info=False):
            """Check that something is logged."""
            for rec in self.records:
                if rec.levelname == level and str(msg) in rec.getMessage():
                    if with_exc_info:
                        return rec.exc_info is not None
                    return True
            return False

    def setUp(self):
        """Add the memento handler to the root logger."""
        super(LogHandlerTestCase, self).setUp()
        self.memento_handler = self.MementoHandler()
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.INFO)
        self.root_logger.addHandler(self.memento_handler)
        self.old_block_tor = settings.USER_BLOCK_TOR_GATEWAY
        self.old_block_email = settings.USER_BLOCK_EMAIL_BLACKLIST

    def tearDown(self):
        """Remove the memento handler from the root logger."""
        self.root_logger.removeHandler(self.memento_handler)
        settings.USER_BLOCK_TOR_GATEWAY = self.old_block_tor
        settings.USER_BLOCK_EMAIL_BLACKLIST = self.old_block_email
        super(LogHandlerTestCase, self).tearDown()

    def assertLogLevelContains(self, level, message, with_exc_info=False):
        # XXX michaeln 2010-08-18 Convert this to use testtools matchers
        # for much better failure output.
        self.assertTrue(
            self.memento_handler.check(level, message, with_exc_info))

    @patch('DNS.DnsRequest')
    def test_client_using_tor(self, mock_dns_request):
        # verify that a client that is a TOR exit node is blocked
        settings.USER_BLOCK_TOR_GATEWAY = True
        request = MockRequest()
        request.META['SERVER_NAME'] = '127.0.0.1'
        request.META['REMOTE_ADDR'] = '127.0.0.2'
        mock_dns_request.return_value.req.side_effect = type(
            'answer', (), {'header': {'status': 'NOERROR'}})
        self.assertTrue(client_using_tor(request))
        self.assertLogLevelContains('INFO', 'Client 127.0.0.2 is using TOR')

    @patch('DNS.DnsRequest')
    def test_client_not_using_tor(self, mock_dns_request):
        # verify that a client that is not a TOR exit node is not blocked
        settings.USER_BLOCK_TOR_GATEWAY = True
        request = MockRequest()
        request.META['SERVER_NAME'] = '127.0.0.1'
        request.META['REMOTE_ADDR'] = '127.0.0.2'
        mock_dns_request.return_value.req.side_effect = type(
            'answer', (), {'header': {'status': 'ERROR'}})
        self.assertFalse(client_using_tor(request))
        self.assertFalse(self.memento_handler.check(
            'INFO', 'Client 127.0.0.2 is using TOR'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_blacklisting_logging(self):
        # Ensure that log messages are present when an email is blacklisted
        BadDomain = EmailBlacklist.objects.create(
            domain='bad-domain.com',
        )
        blacklisted_email_domain('tester@bad-domain.com')
        self.assertLogLevelContains(
            'INFO', 'User\'s email matches a blacklisted domain')

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_blacklisting_no_logging_for_ok_domains(self):
        # Ensure that logging only happens when an address is blacklisted
        blacklisted_email_domain('tester@good-domain.com')
        self.assertFalse(self.memento_handler.check(
            'INFO', 'User\'s email matches a blacklisted domain'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_blacklisted_email_domain_are_blocked(self):
        # Make sure e-mails with blacklisted domains are blocked
        BadDomain = EmailBlacklist.objects.create(
            domain='bad-domain.com',
        )
        self.assertTrue(blacklisted_email_domain('tester@bad-domain.com'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_non_blacklisted_email_domain_not_blocked(self):
        # Make sure e-mails with non-blacklisted domains are allowed
        self.assertFalse(blacklisted_email_domain('tester@good-domain.com'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_blacklisted_email_3rdlevel_domain_are_blocked(self):
        # Make sure e-mails with blacklisted 2nd level domain are blocked
        # even if there is a 3rd level portion
        BadDomain = EmailBlacklist.objects.create(
            domain='bad-domain.com',
        )
        self.assertTrue(blacklisted_email_domain('tester@abc.bad-domain.com'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_non_blacklisted_email_3rdlevel_domain_not_blocked(self):
        # Make sure e-mails with non-blacklisted domains are allowed
        self.assertFalse(blacklisted_email_domain('tester@abc.good-domain.com'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_blacklisted_email_4thlevel_domain_are_blocked(self):
        # Make sure e-mails with blacklisted 2nd level domains are blocked
        # even if the email address contains a 4th level domain portion
        BadDomain = EmailBlacklist.objects.create(
            domain='bad-domain.com',
        )
        self.assertTrue(blacklisted_email_domain('tester@xyz.abc.bad-domain.com'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_non_blacklisted_email_4thlevel_domain_not_blocked(self):
        # Make sure e-mails with non-blacklisted domains are allowed
        self.assertFalse(blacklisted_email_domain('tester@xyz.abc.good-domain.com'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_non_blacklisted_email_tld_not_blocked(self):
        # Make sure e-mails of the form @gmail.ru are not blocked if @mail.ru is
        BadDomain = EmailBlacklist.objects.create(
            domain='mail.ru',
        )
        self.assertFalse(blacklisted_email_domain('tester@gmail.ru'))

    @patch('trial.auth.settings.USER_BLOCK_EMAIL_BLACKLIST', True)
    def test_blacklisted_email_domain_requires_email(self):
        # Ensure that blank e-mails are not tested
        self.assertFalse(blacklisted_email_domain(''))


class CampaignLevelTestCase(DjangoTestCase):
    """Test active campaign instance levels for low markers"""

    def setUp(self):
        self.patch_report = patch(
            'trial.management.commands.check_remaining_instances.report')
        self.patch_exit = patch(
            'trial.management.commands.check_remaining_instances.exit')
        self.patch_filter = patch(
            'trial.models.Campaign.objects.filter')

        self.mock_report = self.patch_report.start()
        self.mock_exit = self.patch_exit.start()
        self.mock_filter = self.patch_filter.start()

        self.campaign_mock = Mock()
        self.campaign_mock.name = 'test_mock'
        self.campaign_mock.remaining_level = Mock()
        self.campaign_mock.remaining_level.return_value = 100.0
        self.campaign_mock.max_instances = 100

        self.mock_filter.return_value = [self.campaign_mock]

    def tearDown(self):
        self.patch_report.stop()
        self.patch_exit.stop()
        self.patch_filter.stop()

    def test_no_campaigns(self):
        self.mock_filter.return_value = {}

        cmd = Command()
        cmd.handle()

        self.mock_exit.assert_called_once_with(1)
        msgs = 'There are currently no active campaigns.'
        self.mock_report.assert_called_once_with(msgs)

    def test_warning_level_10_percent(self):
        self.campaign_mock.remaining_level.return_value = 0.1

        cmd = Command()
        cmd.handle()

        self.mock_exit.assert_called_once_with(1)
        msgs = ['Warning: The campaign, test_mock, '
                'has 10% or less of its instances remaining.']
        self.mock_report.assert_called_once_with(msgs)

    def test_critical_level_5_percent(self):
        self.campaign_mock.remaining_level.return_value = 0.05

        cmd = Command()
        cmd.handle()

        self.mock_exit.assert_called_once_with(1)
        msgs = ['Critical: The campaign, test_mock, '
                'has 5% or less of its instances remaining.']
        self.mock_report.assert_called_once_with(msgs)

    def test_critical_0_instances(self):
        self.campaign_mock.remaining_level.return_value = 0

        cmd = Command()
        cmd.handle()

        self.mock_exit.assert_called_once_with(1)
        msgs = ['Critical: The campaign, test_mock, '
                'has none of its instances remaining.']
        self.mock_report.assert_called_once_with(msgs)

    def test_error_max_instances_0(self):
        self.campaign_mock.max_instances = 0

        cmd = Command()
        cmd.handle()

        self.mock_exit.assert_called_once_with(1)
        msgs = ['Critical: The campaign, test_mock, '
                'has max_instances set to 0. This is likely '
                'a configuration error.']
        self.mock_report.assert_called_once_with(msgs)

    def test_good_level(self):
        self.campaign_mock.remaining_level.return_value = 0.5

        cmd = Command()
        cmd.handle()

        self.mock_exit.assert_called_once_with(0)
        self.mock_report.call_count = 0


class CampaignTestCase(DjangoTestCase):
    """Test campaign model and internal methods"""

    def setUp(self):
        self.user = User.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.org',
            date_joined=datetime.datetime.now()
        )

        self.campaign = Campaign.objects.create(
            name='test-campaign',
            verbose_name='Test Campaign',
            max_instances=5,
            active=True,
        )

        for i in range(4):
            instance = Instances.objects.create(
                instance_id='instance_%d' % i,
                campaign=self.campaign,
                reservation_time=datetime.datetime.now(),
                running_time=datetime.datetime.now(),
                hostname='testing.localhost',
                ip='127.0.0.1',
                secret='12345678',
                owner=self.user
            ).save()

    def test_remaining_method(self):
        self.assertEquals(self.campaign.remaining(), 1)

    def test_remaining_level_method(self):
        self.assertEquals(self.campaign.remaining_level(), 0.2)

    def test_remaining_level_zero(self):
        campaign = Campaign.objects.create(
            name='test-campaign', max_instances=0)
        self.assertEquals(campaign.remaining_level(), 0)


class MailAliasAuthTestCase(DjangoTestCase):

    def test_instance_available_on_first_visit(self):
        campaign = make_campaign()
        email = 'user+1@gmail.com'
        user = make_user(email=email)
        profile = user.get_profile() 
        GmailAlias.save_gmail_alias(email, user)
        self.assertTrue(profile.can_start_trial(campaign.name))

    def test_instance_denied_on_second_visit(self):
        campaign = make_campaign()
        email = 'user+1@gmail.com'
        user = make_user(email=email)
        profile = user.get_profile() 
        GmailAlias.save_gmail_alias(email, user)
        make_instance(user, campaign)
        self.assertFalse(profile.can_start_trial(campaign.name))

    def test_user_for_existing_alias_is_retrieved(self):
        email = 'user+1@gmail.com'
        user = make_user(email=email)
        GmailAlias.save_gmail_alias(user.email, user)
        self.assertEquals(user, GmailAlias.registered_gmail_alias(email))

    def test_no_user_returned_if_no_alias(self):
        email = 'user+1@gmail.com'
        self.assertEquals(None, GmailAlias.registered_gmail_alias(email))

    def test_non_gmail_address(self):
        email = 'user@canonical.com'
        self.assertEquals(False, GmailAlias.is_gmail_address(email))
                
    def test_clean_gmail_address(self):
        email = 'jane.doe+aliasname@gmail.com'
        self.assertEquals('janedoe', GmailAlias.clean_gmail_user(email))

    def user_can_start_trial(self):
        campaign = make_campaign()
        email = 'user@test.com'
        user = make_user(email=email)
        profile = user.get_profile() 
        self.assertTrue(profile.can_start_trial(campaign.name))

    def user_cannot_start_trial(self):
        campaign = make_campaign()
        email = 'user@test.com'
        user = make_user(email=email)
        profile = user.get_profile()
        make_instance(user, campaign)
        self.assertFalse(profile.can_start_trial(campaign.name))
