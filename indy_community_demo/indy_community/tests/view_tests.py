from django.contrib.auth import get_user_model
from django.test import TestCase, Client, modify_settings, override_settings
from django.core import management
from django.core.management.base import CommandError
from django.utils.six import StringIO

from ..utils import *
from ..wallet_utils import *
from ..models import *
from ..views import *
from ..forms import *
import indy_community.management.commands.loads_schemas

User = get_user_model()


class IndyViewsTests(TestCase):
    PASSWORD = 'exampl12345'

    def login_user(self, user_name, raw_password):
        url = reverse('login')
        resp = self.client.post(url, {'username': user_name, 'password': raw_password, 'next': '/individual/profile/'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    def login_org_user(self, user_name, raw_password):
        url = reverse('login')
        resp = self.client.post(url, {'username': user_name, 'password': raw_password, 'next': '/organization/profile/'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    def register_and_login_user(self, user_name, raw_password, first_name, last_name):
        # register
        url = reverse('signup')
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        data = {'first_name': first_name, 'last_name': last_name, 'email': user_name, 
                'password1': raw_password, 'password2': raw_password}
        form = UserSignUpForm(data=data)
        self.assertTrue(form.is_valid())

        url = reverse('signup')
        resp = self.client.post(url, data, follow=True)

        self.login_user(user_name, raw_password)

    def register_and_login_org(self, user_name, raw_password, first_name, last_name, org_name, org_role):
        # register
        url = reverse('signup')
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        data = {'first_name': first_name, 'last_name': last_name, 'email': user_name, 
                'password1': raw_password, 'password2': raw_password,
                'org_name': org_name, 'org_role_name': org_role}
        form = OrganizationSignUpForm(data=data)
        self.assertTrue(form.is_valid())

        url = reverse('org_signup')
        resp = self.client.post(url, data, follow=True)

        self.login_org_user(user_name, raw_password)

    def logout_user(self):
        url = reverse('logout')
        resp = self.client.post(url, follow=True)

    def cleanup_user(self, user, raw_password):
        self.logout_user()

        # cleanup after ourselves
        user_wallet_name = user.wallet.wallet_name
        res = delete_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)

    def cleanup_user_and_org(self, user, org, raw_password):
        self.logout_user()

        # cleanup after ourselves
        org_wallet_name = org.wallet.wallet_name
        res = delete_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)


    def test_register_user_and_login(self):
        USER_USER = 'user_' + random_alpha_string(10) + '@mail.com'

        self.register_and_login_user(USER_USER, self.PASSWORD, 'Random', 'Name')

        # asserts
        url = reverse('individual:profile')
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        fetch_users = User.objects.filter(email=USER_USER).all()
        self.assertEqual(1, len(fetch_users))

        self.cleanup_user(fetch_users[0], self.PASSWORD)


    def test_register_org_user_and_login(self):
        ORG_USER = 'org_' + random_alpha_string(10) + '@mail.com'
        ORG_NAME = 'Org ' + random_alpha_string(10) + ' Inc'

        self.register_and_login_org(ORG_USER, self.PASSWORD, 'Random', 'Name', ORG_NAME, 'Trustee')
        
        # asserts
        url = reverse('organization:profile')
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        fetch_users = User.objects.filter(email=ORG_USER).all()
        self.assertEqual(1, len(fetch_users))
        fetch_orgs = IndyOrganization.objects.filter(org_name=ORG_NAME).all()
        self.assertEqual(1, len(fetch_orgs))

        self.cleanup_user_and_org(fetch_users[0], fetch_orgs[0], self.PASSWORD)

    def test_register_orgs_with_schemas(self):
        ORG_USER = 'org_' + random_alpha_string(10) + '@mail.com'
        ORG_NAME = 'Org ' + random_alpha_string(10) + ' Inc'

        self.register_and_login_org(ORG_USER, self.PASSWORD, 'Random', 'Name', ORG_NAME, 'Trustee')
        self.logout_user()

        fetch_users = User.objects.filter(email=ORG_USER).all()
        self.assertEqual(1, len(fetch_users))
        fetch_orgs = IndyOrganization.objects.filter(org_name=ORG_NAME).all()
        self.assertEqual(1, len(fetch_orgs))

        # load schemas and cred defs from yml config
        config = './imms-schemas.yml'
        out = StringIO()
        management.call_command('loads_schemas', config, str(fetch_orgs[0].id), stdout=out)

        schemas = IndySchema.objects.all()
        self.assertEqual(4, len(schemas))
        proofs = IndyProofRequest.objects.all()
        self.assertEqual(4, len(proofs))

        # load orgs and cred defs from yml config
        config = './imms-orgs.yml'
        out = StringIO()
        management.call_command('loads_orgs', config, stdout=out)

        orgs = IndyOrganization.objects.all()
        self.assertEqual(4, len(orgs))
        cred_defs = IndyCredentialDefinition.objects.all()
        self.assertEqual(4, len(cred_defs))

        # TODO fetch the org for each role

        # TODO register a user Alice

        # TODO issue credentials and proofs ...

        # TODO cleanup - delete all wallets

        self.login_org_user(ORG_USER, self.PASSWORD)
        self.cleanup_user_and_org(fetch_users[0], fetch_orgs[0], self.PASSWORD)

