import asyncio
from pathlib import Path
from tempfile import gettempdir
from os import environ
import asyncio
import aiohttp

from django.apps import AppConfig
from ctypes import *

import time

import json

import sys
from ctypes import *

from indy import anoncreds, crypto, did, ledger, pool, wallet
from indy.error import ErrorCode, IndyError

from django.conf import settings

from .indy_state import set_pool_handle


PROTOCOL_VERSION = 2


def path_home() -> Path:
    return Path.home().joinpath(".indy_client")


async def _fetch_url(the_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(the_url) as resp:
            r_status = resp.status
            r_text = await resp.text()
            return (r_status, r_text)

async def _fetch_genesis_txn(genesis_url: str) -> bool:
    try:
        (r_status, data) = await _fetch_url(genesis_url)
    except:
        raise

    # check data is valid json
    lines = data.splitlines()
    if not lines or not json.loads(lines[0]):
        raise Exception("Genesis transaction file is not valid JSON")

    return data


# this is the genesis that connects to the default indy-sdk ledger, checkout indy-sdk and run:
#    docker build -f ci/indy-pool.dockerfile -t indy_pool .
#    docker run -itd -p 9701-9708:9701-9708 indy_pool
async def pool_genesis_txn_data():
    if 'vcx_genesis_url' in settings.INDY_CONFIG:
        # download from the genesis url, if specified
        genesis_url = settings.INDY_CONFIG['vcx_genesis_url']
        genesis_txn = await _fetch_genesis_txn(genesis_url)
    else:
        # this is the default if not specified
        pool_ip = environ.get("TEST_POOL_IP", "127.0.0.1")

        genesis_txn = "\n".join([
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node1","blskey":"4N8aUNHSgjQVgkpm8nhNEfDf6txHznoYREg9kirmJrkivgL4oSEimFF6nsQ6M41QvhM2Z33nves5vfSn9n1UwNFJBYtWVnHYMATn76vLuL3zU88KyeAYcHfsih3He6UHcXDxcaecHVz6jhCYz1P2UZn2bDVruL5wXpehgBfBaLKm3Ba","blskey_pop":"RahHYiCvoNCtPTrVtP7nMC5eTYrsUA8WjXbdhNc8debh1agE9bGiJxWBXYNFbnJXoXhWFMvyqhqhRoq737YQemH5ik9oL7R4NTTCz2LEZhkgLJzB3QRQqJyBNyv7acbdHrAT8nQ9UkLbaVL9NBpnWXBTw4LEMePaSHEw66RzPNdAX1","client_ip":"{}","client_port":9702,"node_ip":"{}","node_port":9701,"services":["VALIDATOR"]}},"dest":"Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv"}},"metadata":{{"from":"Th7MpTaRZVRYnPiabds81Y"}},"type":"0"}},"txnMetadata":{{"seqNo":1,"txnId":"fea82e10e894419fe2bea7d96296a6d46f50f93f9eeda954ec461b2ed2950b62"}},"ver":"1"}}'.format(
                pool_ip, pool_ip),
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node2","blskey":"37rAPpXVoxzKhz7d9gkUe52XuXryuLXoM6P6LbWDB7LSbG62Lsb33sfG7zqS8TK1MXwuCHj1FKNzVpsnafmqLG1vXN88rt38mNFs9TENzm4QHdBzsvCuoBnPH7rpYYDo9DZNJePaDvRvqJKByCabubJz3XXKbEeshzpz4Ma5QYpJqjk","blskey_pop":"Qr658mWZ2YC8JXGXwMDQTzuZCWF7NK9EwxphGmcBvCh6ybUuLxbG65nsX4JvD4SPNtkJ2w9ug1yLTj6fgmuDg41TgECXjLCij3RMsV8CwewBVgVN67wsA45DFWvqvLtu4rjNnE9JbdFTc1Z4WCPA3Xan44K1HoHAq9EVeaRYs8zoF5","client_ip":"{}","client_port":9704,"node_ip":"{}","node_port":9703,"services":["VALIDATOR"]}},"dest":"8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb"}},"metadata":{{"from":"EbP4aYNeTHL6q385GuVpRV"}},"type":"0"}},"txnMetadata":{{"seqNo":2,"txnId":"1ac8aece2a18ced660fef8694b61aac3af08ba875ce3026a160acbc3a3af35fc"}},"ver":"1"}}'.format(
                pool_ip, pool_ip),
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node3","blskey":"3WFpdbg7C5cnLYZwFZevJqhubkFALBfCBBok15GdrKMUhUjGsk3jV6QKj6MZgEubF7oqCafxNdkm7eswgA4sdKTRc82tLGzZBd6vNqU8dupzup6uYUf32KTHTPQbuUM8Yk4QFXjEf2Usu2TJcNkdgpyeUSX42u5LqdDDpNSWUK5deC5","blskey_pop":"QwDeb2CkNSx6r8QC8vGQK3GRv7Yndn84TGNijX8YXHPiagXajyfTjoR87rXUu4G4QLk2cF8NNyqWiYMus1623dELWwx57rLCFqGh7N4ZRbGDRP4fnVcaKg1BcUxQ866Ven4gw8y4N56S5HzxXNBZtLYmhGHvDtk6PFkFwCvxYrNYjh","client_ip":"{}","client_port":9706,"node_ip":"{}","node_port":9705,"services":["VALIDATOR"]}},"dest":"DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya"}},"metadata":{{"from":"4cU41vWW82ArfxJxHkzXPG"}},"type":"0"}},"txnMetadata":{{"seqNo":3,"txnId":"7e9f355dffa78ed24668f0e0e369fd8c224076571c51e2ea8be5f26479edebe4"}},"ver":"1"}}'.format(
                pool_ip, pool_ip),
            '{{"reqSignature":{{}},"txn":{{"data":{{"data":{{"alias":"Node4","blskey":"2zN3bHM1m4rLz54MJHYSwvqzPchYp8jkHswveCLAEJVcX6Mm1wHQD1SkPYMzUDTZvWvhuE6VNAkK3KxVeEmsanSmvjVkReDeBEMxeDaayjcZjFGPydyey1qxBHmTvAnBKoPydvuTAqx5f7YNNRAdeLmUi99gERUU7TD8KfAa6MpQ9bw","blskey_pop":"RPLagxaR5xdimFzwmzYnz4ZhWtYQEj8iR5ZU53T2gitPCyCHQneUn2Huc4oeLd2B2HzkGnjAff4hWTJT6C7qHYB1Mv2wU5iHHGFWkhnTX9WsEAbunJCV2qcaXScKj4tTfvdDKfLiVuU2av6hbsMztirRze7LvYBkRHV3tGwyCptsrP","client_ip":"{}","client_port":9708,"node_ip":"{}","node_port":9707,"services":["VALIDATOR"]}},"dest":"4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA"}},"metadata":{{"from":"TWwCRQRZ2ZHMJFn9TzLp7W"}},"type":"0"}},"txnMetadata":{{"seqNo":4,"txnId":"aa5e817d7cc626170eca175822029339a444eb0ee8f0bd20d3b0b76e566fb008"}},"ver":"1"}}'.format(
                pool_ip, pool_ip)
        ])

    indy_config = getattr(settings, 'INDY_CONFIG')
    f = open(indy_config['vcx_genesis_path'], "w+")
    f.write(genesis_txn)
    f.close()

    return genesis_txn

def run_coroutine(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine())
    finally:
        loop.close()

async def get_pool_genesis_txn_path(pool_name):
    path_temp = Path(gettempdir()).joinpath("indy")
    path = path_temp.joinpath("{}.txn".format(pool_name))
    await save_pool_genesis_txn_file(path)
    return path

async def save_pool_genesis_txn_file(path):
    data = await pool_genesis_txn_data()

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(str(path), "w+") as f:
        f.writelines(data)


class IndyCoreConfig(AppConfig):
    name = 'indy_community'

    def ready(self):
        # import login/logout signals
        import indy_community.signals

        pg_dll = settings.INDY_CONFIG['storage_dll']
        pg_entrypoint = settings.INDY_CONFIG['storage_entrypoint']
        print('Loading {}'.format(pg_dll))
        stg_lib = CDLL(pg_dll)
        result = stg_lib[pg_entrypoint]()
        if result != 0:
            print('Error unable to load wallet storage {}'.format(result))
            raise AppError('Error unable to load wallet storage {}'.format(result))

        pay_dll = settings.INDY_CONFIG['payment_dll']
        pay_entrypoint = settings.INDY_CONFIG['payment_entrypoint']
        print('Loading {}'.format(pay_dll))
        pay_lib = CDLL(pay_dll)
        result = pay_lib[pay_entrypoint]()
        if result != 0:
            print('Error unable to load payment plug-in {}'.format(result))
            raise AppError('Error unable to load payment plug-in {}'.format(result))

        pool_handle = run_coroutine(run)
        set_pool_handle(pool_handle)
        time.sleep(1)  # FIXME waiting for libindy thread complete

        print("App is ready!!!")


async def run():
    print("Getting started -> started")

    pool_ = {
        'name': 'pool1'
    }
    print("Open Pool Ledger: {}".format(pool_['name']))
    pool_['genesis_txn_path'] = await get_pool_genesis_txn_path(pool_['name'])
    print(pool_['genesis_txn_path'])
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})

    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(PROTOCOL_VERSION)

    try:
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    pool_handle = await pool.open_pool_ledger(pool_['name'], None)
    print("Returned pool handle", pool_handle)
    return pool_handle

