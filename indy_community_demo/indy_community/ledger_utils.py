import asyncio
import json
from os import environ
import random

from django.conf import settings

from indy import anoncreds, crypto, did, ledger, pool, wallet
from indy.error import ErrorCode, IndyError

from .utils import *
from .indy_state import get_pool_handle


######################################################################
# basic ledger query utilities
######################################################################
def get_did_info(my_did):
    """
    Lookup DID information on the ledger
    """
    pool_handle = get_pool_handle()

    get_nym_request = run_coroutine_with_args(ledger.build_get_nym_request, my_did, my_did)
    nym_response = run_coroutine_with_args(ledger.submit_request, pool_handle, get_nym_request)
    seq_no = int(json.loads(nym_response)['result']['seqNo'])
    get_txn_request = run_coroutine_with_args(ledger.build_get_txn_request, my_did, "DOMAIN", seq_no)
    txn_response = run_coroutine_with_args(ledger.submit_request, pool_handle, get_nym_request)

    return (nym_response, txn_response)

def get_did_attrib(my_did, attrib):
    """
    Lookup DID attributes on the ledger
    """
    pool_handle = get_pool_handle()

    get_attrib_request = run_coroutine_with_args(ledger.build_get_attrib_request, my_did, my_did, attrib, None, None)
    attrib_response = run_coroutine_with_args(ledger.submit_request, pool_handle, get_attrib_request)

    return attrib_response

def write_new_did(wallet_handle, ledger_did, my_did, verkey, alias, role):
    """
    Write a new DID to the ledger
    """
    pool_handle = get_pool_handle()

    req_json = run_coroutine_with_args(ledger.build_nym_request, ledger_did, my_did, verkey, alias, role)
    rv_json = run_coroutine_with_args(ledger.sign_and_submit_request, pool_handle, wallet_handle, ledger_did, req_json)

def write_did_attrib(wallet_handle, ledger_did, my_did, attrib_raw):
    """
    Add or update a DID attribute on the ledger
    """
    pool_handle = get_pool_handle()

    attrib_request = run_coroutine_with_args(ledger.build_attrib_request, ledger_did, my_did, None, attrib_raw, None)
    run_coroutine_with_args(ledger.sign_and_submit_request, pool_handle, wallet_handle, my_did, attrib_request)

def get_schema_info(my_did, schema_id):
    """
    Read info from the ledger
    """
    pool_handle = get_pool_handle()

    get_schema_request = run_coroutine_with_args(ledger.build_get_schema_request, my_did, schema_id)
    get_schema_response = run_coroutine_with_args(ledger.submit_request, pool_handle, get_schema_request)

    return get_schema_response

def get_cred_def_info(my_did, cred_def_id):
    """
    Read info from the ledger
    """
    pool_handle = get_pool_handle()

    get_cred_def_request = run_coroutine_with_args(ledger.build_get_cred_def_request, my_did, cred_def_id)
    get_cred_def_response = run_coroutine_with_args(ledger.submit_request, pool_handle, get_cred_def_request)

    return get_cred_def_response


