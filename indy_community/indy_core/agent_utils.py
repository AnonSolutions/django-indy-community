import asyncio
import aiohttp
import json
from os import environ
from pathlib import Path
from tempfile import gettempdir
import random

from django.conf import settings

from indy.error import ErrorCode, IndyError

from vcx.api.connection import Connection
from vcx.api.schema import Schema
from vcx.api.credential_def import CredentialDef
from vcx.api.credential import Credential
from vcx.state import State, ProofState
from vcx.api.disclosed_proof import DisclosedProof
from vcx.api.issuer_credential import IssuerCredential
from vcx.api.proof import Proof
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.common import shutdown

from .utils import *


DUMMY_SEED = "00000000000000000000000000000000"

def vcx_provision_config(wallet_name, raw_password, institution_name, did_seed=None, org_role='', institution_logo_url='http://robohash.org/456'):
    """
    Build a configuration objects for a VCX environment or agent
    """
    provisionConfig = {
        'agency_url': settings.INDY_CONFIG['vcx_agency_url'],
        'agency_did': settings.INDY_CONFIG['vcx_agency_did'],
        'agency_verkey': settings.INDY_CONFIG['vcx_agency_verkey'],
        'pool_name': 'pool_' + wallet_name,
        'wallet_type': 'postgres_storage',
        'wallet_name': wallet_name,
        'wallet_key': raw_password,
        'storage_config': json.dumps(settings.INDY_CONFIG['storage_config']),
        'storage_credentials': json.dumps(settings.INDY_CONFIG['storage_credentials']),
        'payment_method': settings.INDY_CONFIG['vcx_payment_method'],
    }

    # role-dependant did seed
    if did_seed and 0 < len(did_seed):
        provisionConfig['enterprise_seed'] = did_seed
    else:
        provisionConfig['enterprise_seed'] = DUMMY_SEED

    provisionConfig['institution_name'] = institution_name
    provisionConfig['institution_logo_url'] = institution_logo_url
    provisionConfig['genesis_path'] = settings.INDY_CONFIG['vcx_genesis_path']
    provisionConfig['pool_name'] = 'pool_' + wallet_name

    return provisionConfig


def initialize_and_provision_vcx(wallet_name, raw_password, institution_name, did_seed=None, org_role='', institution_logo_url='http://robohash.org/456'):
    provisionConfig = vcx_provision_config(wallet_name, raw_password, institution_name, did_seed=did_seed, org_role=org_role, institution_logo_url=institution_logo_url)

    print(" >>> Provision an agent and wallet, get back configuration details")
    try:
        provisionConfig_json = json.dumps(provisionConfig)
        config = run_coroutine_with_args(vcx_agent_provision, provisionConfig_json)
    except:
        raise

    config = json.loads(config)

    # Set some additional configuration options specific to alice
    config['institution_name'] = institution_name
    config['institution_logo_url'] = institution_logo_url
    config['genesis_path'] = settings.INDY_CONFIG['vcx_genesis_path']
    config['pool_name'] = 'pool_' + wallet_name

    print(" >>> Initialize libvcx with new configuration for", institution_name)
    try:
        config_json = json.dumps(config)
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return json.dumps(config)


