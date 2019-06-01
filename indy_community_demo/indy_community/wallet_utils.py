import asyncio
import aiohttp
import json
from os import environ
import random

from django.conf import settings

from indy import anoncreds, crypto, did, ledger, pool, wallet
from indy.error import ErrorCode, IndyError
from indy.anoncreds import prover_search_credentials, prover_fetch_credentials, prover_close_credentials_search

from .models import *
from .utils import *


######################################################################
# basic wallet management utilities
######################################################################
def get_user_wallet_name(username):
    """
    Determine wallet name based on a user name (email).
    """

    wallet_name = username.replace("@", "_")
    wallet_name = wallet_name.replace(".", "_")
    return 'i_{}'.format(wallet_name).lower()


def get_org_wallet_name(orgname):
    """
    Determine wallet name based on an organization name.
    """

    wallet_name = orgname.replace("@", "_")
    wallet_name = wallet_name.replace(".", "_")
    wallet_name = wallet_name.replace(" ", "_")
    return 'o_{}'.format(wallet_name).lower()


def create_wallet(wallet_name, raw_password):
    """
    Create an Indy wallet (postgres).
    """

    wallet_config_json = wallet_config(wallet_name)
    wallet_credentials_json = wallet_credentials(raw_password)
    try:
        run_coroutine_with_args(wallet.create_wallet, wallet_config_json, wallet_credentials_json)
    except IndyError as ex:
        if ex.error_code == ErrorCode.WalletAlreadyExistsError:
            return 0
        return error_code
    return 0

def delete_wallet(wallet_name, raw_password):
    """
    Delete an Indy wallet (postgres).
    """

    wallet_config_json = wallet_config(wallet_name)
    wallet_credentials_json = wallet_credentials(raw_password)
    try:
        run_coroutine_with_args(wallet.delete_wallet, wallet_config_json, wallet_credentials_json)
    except IndyError as ex:
        return error_code
    return 0


def open_wallet(wallet_name, raw_password):
    """
    Open an Indy wallet (postgres).
    """

    wallet_config_json = wallet_config(wallet_name)
    wallet_credentials_json = wallet_credentials(raw_password)
    try:
        wallet_handle = run_coroutine_with_args(wallet.open_wallet, wallet_config_json, wallet_credentials_json)
        return wallet_handle
    except IndyError as ex:
        return error_code


def close_wallet(wallet_handle):
    """
    Close an Indy wallet (postgres).
    """

    try:
        run_coroutine_with_args(wallet.close_wallet, wallet_handle)
        return 0
    except IndyError as ex:
        return error_code


def wallet_config(wallet_name):
    """
    Build a wallet configuration dictionary (postgres specific).
    """

    storage_config = settings.INDY_CONFIG['storage_config']
    wallet_config = settings.INDY_CONFIG['wallet_config']
    wallet_config['id'] = wallet_name
    wallet_config['storage_config'] = storage_config
    wallet_config_json = json.dumps(wallet_config)
    return wallet_config_json


def wallet_credentials(raw_password):
    """
    Build wallet credentials dictionary (postgres specific).
    """

    storage_credentials = settings.INDY_CONFIG['storage_credentials']
    wallet_credentials = settings.INDY_CONFIG['wallet_credentials']
    wallet_credentials['key'] = raw_password
    wallet_credentials['storage_credentials'] = storage_credentials
    wallet_credentials_json = json.dumps(wallet_credentials)
    return wallet_credentials_json


def list_wallet_credentials(wallet):
    """
    List all credentials in the current wallet.
    """

    # for now, we have our secret password in our wallet config
    wallet_name = wallet.wallet_name
    wallet_config = json.loads(wallet.wallet_config)
    raw_password = wallet_config['wallet_key']
    wallet_handle = open_wallet(wallet_name, raw_password)

    (search_handle, search_count) = run_coroutine_with_args(prover_search_credentials, wallet_handle, "{}")
    credentials = run_coroutine_with_args(prover_fetch_credentials, search_handle, search_count)
    run_coroutine_with_args(prover_close_credentials_search, search_handle)

    close_wallet(wallet_handle)

    return json.loads(credentials)


######################################################################
# basic wallet storage utilities (non-secrets interface)
######################################################################


