import asyncio
import aiohttp
import json
from os import environ
from pathlib import Path
from tempfile import gettempdir
import random
import uuid

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

from .models import *
from .utils import *



DUMMY_SEED = "00000000000000000000000000000000"

######################################################################
# utilities to provision vcx agents
######################################################################
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


######################################################################
# utilities to create schemas and credential defitions
######################################################################

def create_schema_json(schema_name, schema_version, schema_attrs):
    """
    Create a schema object based on a list of attributes
    Returns the schema as well as a template for creating credentials
    """
    schema = {
        'name': schema_name,
        'version': schema_version,
        'attributes': schema_attrs
    }
    creddef_template = {}
    for attr in schema_attrs:
        creddef_template[attr] = ''

    return (json.dumps(schema), json.dumps(creddef_template))


# TODO for now just create a random schema and creddef
def create_schema(wallet, schema_json, schema_template):
    """
    Create a schema (VCX) and also store in our local database
    """
    print(" >>> Initialize libvcx with trustee configuration")
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    try:
        schema = json.loads(schema_json)
        vcxschema = run_coroutine_with_args(Schema.create, 'schema_uuid', schema['name'], schema['version'], schema['attributes'], 0)
        schema_id = run_coroutine(vcxschema.get_schema_id)
        schema_data = run_coroutine(vcxschema.serialize)

        indy_schema = IndySchema(
                            ledger_schema_id = schema_id,
                            schema_name = schema['name'],
                            schema_version = schema['version'],
                            schema = schema_data,
                            schema_template = schema_template,
                            schema_data = json.dumps(schema_data)
                            )
        indy_schema.save()

    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    return indy_schema


# TODO for now just create a random schema and creddef
def create_creddef(wallet, indy_schema, creddef_name, creddef_template):
    """
    Create a credential definition (VCX) and also store in our local database
    """
    # wallet specific-configuration for creatig the cred def
    print(" >>> Initialize libvcx with wallet-specific configuration")
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    try:
        cred_def = run_coroutine_with_args(CredentialDef.create, 'credef_uuid', creddef_name, indy_schema.ledger_schema_id, 0)
        cred_def_handle = cred_def.handle
        cred_def_id = run_coroutine(cred_def.get_cred_def_id)
        creddef_data = run_coroutine(cred_def.serialize)

        indy_creddef = IndyCredentialDefinition(
                            ledger_creddef_id = cred_def_id,
                            ledger_schema = indy_schema,
                            wallet = wallet,
                            creddef_name = creddef_name,
                            creddef_handle = cred_def_handle,
                            creddef_template = creddef_template,
                            creddef_data = json.dumps(creddef_data)
                            )
        indy_creddef.save()

    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")

    return indy_creddef


def create_proof_request(name, description, attrs, predicates):
    """
    Create a proof request template (local database only)
    """
    proof_req_attrs = json.dumps(attrs)
    proof_req_predicates = json.dumps(predicates)
    proof_request = IndyProofRequest(
                            proof_req_name = name,
                            proof_req_description = description,
                            proof_req_attrs = proof_req_attrs,
                            proof_req_predicates = proof_req_predicates
                            )
    proof_request.save()

    return proof_request


######################################################################
# utilities to create and confirm agent-to-agent connections
######################################################################

def send_connection_invitation(wallet, partner_name):
    print(" >>> Initialize libvcx with new configuration for a connection to", partner_name)
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        connection_to_ = run_coroutine_with_args(Connection.create, partner_name)
        run_coroutine_with_args(connection_to_.connect, '{"use_public_did": true}')
        run_coroutine(connection_to_.update_state)
        invite_details = run_coroutine_with_args(connection_to_.invite_details, False)

        connection_data = run_coroutine(connection_to_.serialize)
        connection_to_.release()
        connection_to_ = None

        connection = AgentConnection(
            wallet = wallet,
            partner_name = partner_name,
            invitation = json.dumps(invite_details),
            token = str(uuid.uuid4()),
            connection_type = 'Outbound',
            connection_data = json.dumps(connection_data),
            status = 'Sent')
        connection.save()
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return connection


def send_connection_confirmation(wallet, partner_name, invite_details):
    print(" >>> Initialize libvcx with configuration")
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        connection_from_ = run_coroutine_with_args(Connection.create_with_details, partner_name, invite_details)
        run_coroutine_with_args(connection_from_.connect, '{"use_public_did": true}')
        run_coroutine(connection_from_.update_state)

        connection_data = run_coroutine(connection_from_.serialize)
        connection_from_.release()
        connection_from_ = None

        connections = AgentConnection.objects.filter(wallet=wallet, partner_name=partner_name).all()
        if 0 < len(connections):
            connection = connections[0]
            connection.connection_data = json.dumps(connection_data)
            connection.status = 'Active'
        else:
            connection = AgentConnection(
                wallet = wallet,
                partner_name = partner_name,
                invitation = invite_details,
                connection_type = 'Inbound',
                connection_data = json.dumps(connection_data),
                status = 'Active')
        connection.save()
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return connection


def check_connection_status(wallet, connection):
    print(" >>> Initialize libvcx with configuration")
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and check status
    try:
        connection_to_ = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))
        run_coroutine(connection_to_.update_state)
        connection_state = run_coroutine(connection_to_.get_state)
        if connection_state == State.Accepted:
            return_state = 'Active'
        else:
            return_state = 'Sent'

        connection_data = run_coroutine(connection_to_.serialize)
        connection_to_.release()
        connection_to_ = None

        connections = AgentConnection.objects.filter(wallet=wallet, status='Sent', partner_name=connection.partner_name).all()
        my_connection = connections[0]
        my_connection.connection_data = json.dumps(connection_data)
        my_connection.status = return_state
        my_connection.save()
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return my_connection


######################################################################
# utilities to offer, request, send and receive credentials
######################################################################

def send_credential_offer(wallet, connection, credential_tag, schema_attrs, cred_def, credential_name):
    print(" >>> Initialize libvcx with new configuration for a cred offer to", connection.partner_name)
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))
        my_cred_def = run_coroutine_with_args(CredentialDef.deserialize, json.loads(cred_def.creddef_data))
        cred_def_handle = my_cred_def.handle

        # create a credential (the last '0' is the 'price')
        credential = run_coroutine_with_args(IssuerCredential.create, credential_tag, schema_attrs, int(cred_def_handle), credential_name, '0')

        print("Issue credential offer to", connection.partner_name)
        run_coroutine_with_args(credential.send_offer, my_connection)

        # serialize/deserialize credential - waiting for Alice to rspond with Credential Request
        credential_data = run_coroutine(credential.serialize)

        conversation = AgentConversation(
            wallet = wallet,
            connection_partner_name = connection.partner_name,
            conversation_type = 'CredentialOffer',
            message_id = 'N/A',
            status = 'Sent',
            conversation_data = json.dumps(credential_data))
        conversation.save()
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return conversation
    

def send_credential_request(wallet, connection, conversation):
    print(" >>> Initialize libvcx with new configuration for a cred offer to", connection.partner_name)
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))
        #my_offer = run_coroutine_with_args()
    
        print("Create a credential object from the credential offer")
        offer_json = [json.loads(conversation.conversation_data),]
        credential = run_coroutine_with_args(Credential.create, 'credential', offer_json)

        print("After receiving credential offer, send credential request")
        run_coroutine_with_args(credential.send_request, my_connection, 0)

        # serialize/deserialize credential - wait for Faber to send credential
        credential_data = run_coroutine(credential.serialize)

        conversation.status = 'Sent'
        conversation.conversation_data = json.dumps(credential_data)
        conversation.conversation_type = 'CredentialRequest'
        conversation.save()
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return conversation


######################################################################
# utilities to request, send and receive proofs
######################################################################

def send_proof_request(wallet, connection, proof_uuid, proof_name, proof_attrs, proof_predicates):
    print(" >>> Initialize libvcx with new configuration for a cred offer to", connection.partner_name)
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))

        # create a proof request
        proof = run_coroutine_with_kwargs(Proof.create, proof_uuid, proof_name, proof_attrs, {}, requested_predicates=proof_predicates)

        proof_data = run_coroutine(proof.serialize)

        run_coroutine_with_args(proof.request_proof, my_connection)

        # serialize/deserialize credential - waiting for Alice to rspond with Credential Request
        proof_data = run_coroutine(proof.serialize)

        conversation = AgentConversation(
            wallet = wallet,
            connection_partner_name = connection.partner_name,
            conversation_type = 'ProofRequest',
            message_id = 'N/A',
            status = 'Sent',
            conversation_data = json.dumps(proof_data))
        conversation.save()
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return conversation


def get_claims_for_proof_request(wallet, connection, my_conversation):
    print(" >>> Initialize libvcx with new configuration for a cred offer to", connection.partner_name)
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))

        # create a proof request
        proof = run_coroutine_with_args(DisclosedProof.create, 'proof', json.loads(my_conversation.conversation_data))

        creds_for_proof = run_coroutine(proof.get_creds)
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return creds_for_proof


def cred_for_referent(creds_for_proof, attr, schema_id):
    for cred in creds_for_proof['attrs'][attr]:
        if schema_id == cred['cred_info']['referent']:
            return cred
    return None

def send_claims_for_proof_request(wallet, connection, my_conversation, credential_attrs):
    print(" >>> Initialize libvcx with new configuration for a cred offer to", connection.partner_name)
    try:
        config_json = wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    # create connection and generate invitation
    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))

        # load proof request
        proof = run_coroutine_with_args(DisclosedProof.create, 'proof', json.loads(my_conversation.conversation_data))
        creds_for_proof = run_coroutine(proof.get_creds)

        self_attested = {}
        for attr in creds_for_proof['attrs']:
            selected = credential_attrs[attr]
            print(attr, selected)
            if 'referent' in selected:
                creds_for_proof['attrs'][attr] = {
                    'credential': cred_for_referent(creds_for_proof, attr, selected['referent'])
                }
            else:
                self_attested[attr] = selected['value']

        for attr in self_attested:
            del creds_for_proof['attrs'][attr]

        # generate and send proof
        run_coroutine_with_args(proof.generate_proof, creds_for_proof, self_attested)
        run_coroutine_with_args(proof.send_proof, my_connection)

        # serialize/deserialize proof 
        proof_data = run_coroutine(proof.serialize)

        my_conversation.status = 'Accepted'
        my_conversation.conversation_type = 'ProofOffer'
        my_conversation.conversation_data = json.dumps(proof_data)
        my_conversation.save()

    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")
    return proof_data


######################################################################
# utilities to poll for and process outstanding messages
######################################################################

def handle_inbound_messages(my_wallet, my_connection):
    print(" >>> Initialize libvcx with configuration")
    try:
        config_json = my_wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    try:
        handled_count = 0
        connection_data = json.loads(my_connection.connection_data)
        connection_to_ = run_coroutine_with_args(Connection.deserialize, connection_data)

        if my_connection.connection_type == 'Inbound':
            print(" >>> Check for and receive offers")
            offers = run_coroutine_with_args(Credential.get_offers, connection_to_)
            for offer in offers:
                already_handled = AgentConversation.objects.filter(message_id=offer[0]['msg_ref_id']).all()
                if len(already_handled) == 0:
                    save_offer = offer[0].copy()
                    offer_data = json.dumps(save_offer)
                    new_offer = AgentConversation(
                                        wallet = my_wallet,
                                        connection_partner_name = my_connection.partner_name,
                                        conversation_type = "CredentialOffer",
                                        message_id = save_offer['msg_ref_id'],
                                        status = 'Pending',
                                        conversation_data = offer_data
                                    )
                    print(" >>> Saving received offer to DB")
                    new_offer.save()
                    handled_count = handled_count + 1

        print(" >>> Check for and handle proof requests")
        requests = run_coroutine_with_args(DisclosedProof.get_requests, connection_to_)
        for request in requests:
            already_handled = AgentConversation.objects.filter(message_id=request['msg_ref_id']).all()
            if len(already_handled) == 0:
                save_request = request.copy()
                request_data = json.dumps(save_request)
                new_request = AgentConversation(
                                    wallet = my_wallet,
                                    connection_partner_name = my_connection.partner_name,
                                    conversation_type = "ProofRequest",
                                    message_id = save_request['msg_ref_id'],
                                    status = 'Pending',
                                    conversation_data = request_data
                                )
                print(" >>> Saving received proof request to DB")
                new_request.save()
                handled_count = handled_count + 1
    except:
        print("Error polling offers and proof requests")
        # TODO ignore polling errors for now ...
        raise
        pass
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!")

    return handled_count


def poll_message_conversation(my_wallet, my_connection, message, initialize_vcx=True):
    if initialize_vcx:
        print(" >>> Initialize libvcx with configuration")
        try:
            config_json = my_wallet.wallet_config
            run_coroutine_with_args(vcx_init_with_config, config_json)
        except:
            raise

    try:
        print(" ... Checking message", message.message_id, message.conversation_type)

        connection = run_coroutine_with_args(Connection.deserialize, json.loads(my_connection.connection_data))

        # handle based on message type and status:
        if message.conversation_type == 'CredentialOffer':
            # offer sent from issuer to individual
            # de-serialize message content
            credential = run_coroutine_with_args(IssuerCredential.deserialize, json.loads(message.conversation_data))

            run_coroutine(credential.update_state)
            credential_state = run_coroutine(credential.get_state)
            print("Updated status = ", credential_state)

            if credential_state == State.RequestReceived:
                print("Sending credential")
                run_coroutine_with_args(credential.send_credential, connection)
                message.conversation_type = 'IssueCredential'
            elif credential_state == State.Accepted:
                message.status = 'Accepted'

            print("Saving message with a status of", message.message_id, message.conversation_type, message.status)
            credential_data = run_coroutine(credential.serialize)
            message.conversation_data = json.dumps(credential_data)
            message.save()
        
        elif message.conversation_type == 'CredentialRequest':
            # cred request sent from individual to offerer
            conversation_data_json = json.loads(message.conversation_data)
            credential = run_coroutine_with_args(Credential.deserialize, conversation_data_json)

            run_coroutine(credential.update_state)
            credential_state = run_coroutine(credential.get_state)
            print("Updated status = ", credential_state)

            if credential_state == State.Accepted:
                message.status = 'Accepted'

            print("Saving message with a status of ", message.message_id, message.conversation_type, message.status)
            credential_data = run_coroutine(credential.serialize)
            message.conversation_data = json.dumps(credential_data)
            message.save()

        elif message.conversation_type == 'IssueCredential':
            # credential sent, waiting for acceptance
            # de-serialize message content
            credential = run_coroutine_with_args(IssuerCredential.deserialize, json.loads(message.conversation_data))

            run_coroutine(credential.update_state)
            credential_state = run_coroutine(credential.get_state)
            print("Updated status = ", credential_state)

            if credential_state == State.Accepted:
                message.status = 'Accepted'

            # serialize/deserialize credential - wait for Faber to send credential
            print("Saving message with a status of ", message.message_id, message.conversation_type, message.status)
            credential_data = run_coroutine(credential.serialize)
            message.conversation_data = json.dumps(credential_data)
            message.save()
        
        elif message.conversation_type == 'ProofRequest':
            # proof request send, waiting for proof offer
            # de-serialize message content
            proof = run_coroutine_with_args(Proof.deserialize, json.loads(message.conversation_data))

            run_coroutine(proof.update_state)
            proof_state = run_coroutine(proof.get_state)
            print("Updated status = ", proof_state)

            if proof_state == State.Accepted:
                message.status = 'Accepted'
                run_coroutine_with_args(proof.get_proof, connection)

                if proof.proof_state == ProofState.Verified:
                    print("proof is verified!!")
                    message.proof_state = 'Verified'
                else:
                    print("could not verify proof :(")
                    message.proof_state = 'Not Verified'

            # serialize/deserialize credential - wait for Faber to send credential
            print("Saving message with a status of ", message.message_id, message.conversation_type, message.status)
            proof_data = run_coroutine(proof.serialize)
            message.conversation_data = json.dumps(proof_data)
            message.save()

        else:
            print("Error unknown conversation type", message.message_id, message.conversation_type)

        pass
    except:
        raise
    finally:
        if initialize_vcx:
            print(" >>> Shutdown vcx (for now)")
            try:
                shutdown(False)
            except:
                raise

    print(" >>> Done!!!")

    return message


def poll_message_conversations(my_wallet, my_connection):
    print(" >>> Initialize libvcx with configuration")
    try:
        config_json = my_wallet.wallet_config
        run_coroutine_with_args(vcx_init_with_config, config_json)
    except:
        raise

    try:
        polled_count = 0

        # Any conversations of status 'Sent' are for bot processing ...
        messages = AgentConversation.objects.filter(wallet=my_wallet, connection_partner_name=my_connection.partner_name, status='Sent')

        for message in messages:
            message = poll_message_conversation(my_wallet, my_connection, message, initialize_vcx=False)
            polled_count = polled_count + 1
            pass
    except:
        raise
    finally:
        print(" >>> Shutdown vcx (for now)")
        try:
            shutdown(False)
        except:
            raise

    print(" >>> Done!!!", polled_count)

    return polled_count

