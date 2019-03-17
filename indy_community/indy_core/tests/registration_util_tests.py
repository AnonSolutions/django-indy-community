from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import *
from ..wallet_utils import *
from ..registration_utils import *


class RegistrationTests(TestCase):

    def test_user_registration(self):
        # create, register and provision a user
        email = 'test1@registration.com'
        user = get_user_model().objects.create(
            email=email,
            first_name='Test',
            last_name='Registration',
        )
        user.save()
        raw_password = 'pass1234'
        user_provision(user, raw_password)

        # fetch and open wallet
        fetch_user = get_user_model().objects.filter(email=email).all()[0]
        user_wallet_name = get_user_wallet_name(email)
        self.assertEqual(fetch_user.wallet.wallet_name, user_wallet_name)
        wallet_handle = open_wallet(user_wallet_name, raw_password)
        res = close_wallet(wallet_handle)
        self.assertEqual(res, 0)

        # cleanup after ourselves
        res = delete_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)


    def test_org_registration(self):
        # create, register and provision a user and org
        # create, register and provision a user
        email = 'test2@registration.com'
        user_wallet_name = get_user_wallet_name(email)
        user = get_user_model().objects.create(
            email=email,
            first_name='Test',
            last_name='Registration',
        )
        user.save()
        raw_password = 'pass1234'
        user_provision(user, raw_password)

        # now org
        org_name = 'My Unittest Org Inc'
        org = org_signup(user, raw_password, org_name)

        # fetch everything ...
        fetch_user = get_user_model().objects.filter(email=email).all()[0]
        fetch_org = IndyOrganization.objects.filter(org_name=org_name).all()[0]
        org_wallet_name = get_org_wallet_name(org_name)
        self.assertEqual(fetch_org.wallet.wallet_name, org_wallet_name)
        wallet_handle = open_wallet(org_wallet_name, raw_password)
        res = close_wallet(wallet_handle)
        self.assertEqual(res, 0)

        # verify relationship
        self.assertEqual(len(fetch_user.indyrelationship_set.all()), 1)
        user_org = fetch_user.indyrelationship_set.all()[0].org
        self.assertEqual(user_org.org_name, org_name)

        self.assertEqual(len(fetch_org.indyrelationship_set.all()), 1)
        org_user = fetch_org.indyrelationship_set.all()[0].user
        self.assertEqual(org_user.email, email)

        # cleanup after ourselves
        res = delete_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)
        res = delete_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)

