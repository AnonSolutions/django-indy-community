from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from indy_community.models import *
from indy_community.wallet_utils import *
from indy_community.utils import *

from ..indy import *
from ..record import *


class WalletStorageTests(TestCase):
    """
    Tests for Indy wallet model class
    """

    def test_wallet_storage_lifecycle(self):
        # create a wallet
        user_name = random_alpha_string(10) + '@mail.com'
        raw_password = 'pass1234'
        user_wallet_name = get_user_wallet_name(user_name)

        # assume that if we run with no exceptions, we are successful
        res = create_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)
        wallet_handle = open_wallet(user_wallet_name, raw_password)

        # open storage and do some stuff
        storage = IndyStorage(wallet_handle=wallet_handle)

        # store a record in non-secrets storage and then retrieve it
        test_record = StorageRecord(type="tester", value='{"Some": "Value", "Probably": "a", "Json": "Structure")', tags={"val1": "Value1", "val2": "Value2"})
        run_coroutine_with_args(storage.add_record, test_record)

        fetch_record = run_coroutine_with_kwargs(storage.get_record, record_type=test_record.type, record_id=test_record.id)

        run_coroutine_with_kwargs(storage.delete_record, record=test_record)

        res = close_wallet(wallet_handle)
        self.assertEqual(res, 0)

        # cleanup after ourselves
        res = delete_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)

