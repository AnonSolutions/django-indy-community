from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..wallet_utils import *
from ..indy_utils import *


class IndyDIDTests(TestCase):
    """
    Tests for creating ledger DID's
    """

    def test_wallet_did_create(self):
        # create a random wallet name
        user_name = random_alpha_string(10) + "@" + random_alpha_string(10) + ".com"
        user_wallet_name = get_user_wallet_name(user_name)
        nym_info = create_and_register_did(user_wallet_name, "NotTrustee")

