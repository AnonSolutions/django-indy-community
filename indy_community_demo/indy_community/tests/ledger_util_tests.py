from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

import json
import time

from indy import anoncreds, crypto, did, ledger, pool, wallet
from indy.error import ErrorCode, IndyError

from ..ledger_utils import *
from ..wallet_utils import *
from ..indy_utils import *
from ..utils import *


LEDGER_SEED = '000000000000000000000000Trustee1'

ANON_DID    = "JGm22KSeapYEa8syXsE41a"
FABER_DID   = "U4mQRtGc7nURTidnkGGZTG"
ACME_DID    = "AhDeQ2udDSAzQzejYoFvc7"
THRIFT_DID  = "S88wA4cvCF8qPBtNndWaes"
BC_PROV_DID = "KtCGSAfKGES32W9wAeLUDA"

SCHEMA_ID   = "JGm22KSeapYEa8syXsE41a:2:Drivers License:27.34.12"
CRED_DEF_ID = "KtCGSAfKGES32W9wAeLUDA:3:CL:15:tag1"


class IndyLedgerTests(TestCase):
    """
    Tests for Indy ledger utility functions
    """

    def test_read_did_info_from_ledger(self):
        (nym_response, txn_response) = get_did_info(ANON_DID)
        #print("nym_response", nym_response)
        #print("txn_response", txn_response)

    def test_read_did_attrib_from_ledger(self):
        attrib_response = get_did_attrib(ANON_DID, "endpoint")
        #print("attrib_response(endpoint)", json.loads(attrib_response))

        attrib_response = get_did_attrib(ANON_DID, "alias")
        #print("attrib_response(alias)", json.loads(attrib_response))

    def test_write_did_attrib(self):
        raw = "{\"endpoint\":{\"ha\":\"127.0.0.1:5555\"}}"

        org_name = 'Some ' + random_alpha_string(10) + ' Inc'
        raw_password = 'pass1234'
        org_wallet_name = get_org_wallet_name(org_name)
        alias = org_name
        role = "TRUST_ANCHOR"

        # assume that if we run with no exceptions, we are successful
        res = create_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)
        wallet_handle = open_wallet(org_wallet_name, raw_password)

        # create a did and write to wallet
        ledger_did_info = json.dumps({'seed': LEDGER_SEED})
        did_info = json.dumps({'seed': calc_wallet_seed(org_name)})
        ledger_did, ledger_verkey = run_coroutine_with_args(did.create_and_store_my_did, wallet_handle, ledger_did_info)
        the_did, verkey = run_coroutine_with_args(did.create_and_store_my_did, wallet_handle, did_info)
        #print("did =", the_did)
        write_new_did(wallet_handle, ledger_did, the_did, verkey, alias, role)
        time.sleep(5)
        (nym_response, txn_response) = get_did_info(the_did)
        #print("nym_response:", nym_response)
        #print("txn_response:", txn_response)

        # now try to write a did attribute to the ledger
        write_did_attrib(wallet_handle, ledger_did, the_did, raw)

        # read it and see what we get
        attrib_response = get_did_attrib(the_did, "endpoint")
        #print("attrib_response(endpoint):", attrib_response)

        # close and delete wallet
        res = close_wallet(wallet_handle)
        self.assertEqual(res, 0)

        # cleanup after ourselves
        res = delete_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)

    def test_read_schema(self):
        schema_response = get_schema_info(ANON_DID, SCHEMA_ID)
        #print("schema", schema_response)

    def test_read_cred_def(self):
        cred_def_response = get_cred_def_info(ANON_DID, CRED_DEF_ID)
        #print("cred_def", cred_def_response)


