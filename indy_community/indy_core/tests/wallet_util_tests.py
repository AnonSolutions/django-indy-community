from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import *
from ..wallet_utils import *


class WalletDBTests(TestCase):
    """
    Tests for Indy wallet model class
    """

    def test_user_wallet_db_lifecycle(self):
        # create a wallet
        user_name = 'user@mail.com'
        raw_password = 'pass1234'
        user_wallet_name = get_user_wallet_name(user_name)

        # assume that if we run with no exceptions, we are successful
        res = create_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)
        wallet_handle = open_wallet(user_wallet_name, raw_password)
        res = close_wallet(wallet_handle)
        self.assertEqual(res, 0)

        # cleanup after ourselves
        res = delete_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)


    def test_org_wallet_db_lifecycle(self):
        # create a wallet
        org_name = 'Some Company Inc'
        raw_password = 'pass1234'
        org_wallet_name = get_org_wallet_name(org_name)

        # assume that if we run with no exceptions, we are successful
        res = create_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)
        wallet_handle = open_wallet(org_wallet_name, raw_password)
        res = close_wallet(wallet_handle)
        self.assertEqual(res, 0)

        # cleanup after ourselves
        res = delete_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)


