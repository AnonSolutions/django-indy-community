from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from django.conf import settings

from time import sleep

from ..models import *
from ..utils import *
from ..wallet_utils import *
from ..registration_utils import *
from ..agent_utils import *


class AgentInteractionTests(TestCase):

    def create_user_and_org(self):
        # create, register and provision a user and org
        # create, register and provision a user
        email = random_alpha_string(10) + "@agent_utils.com"
        user_wallet_name = get_user_wallet_name(email)
        user = get_user_model().objects.create(
            email=email,
            first_name='Test',
            last_name='Registration',
        )
        user.save()
        raw_password = random_alpha_string(8)
        user_provision(user, raw_password)

        # now org
        org_name = 'Agent Utils ' + random_alpha_string(10)
        org = org_signup(user, raw_password, org_name)

        return (user, org, raw_password)

    def establish_agent_connection(self, org, user):
        # send connection request (org -> user)
        org_connection_1 = send_connection_invitation(org.wallet, user.email)
        sleep(1)

        # accept connection request (user -> org)
        user_connection = send_connection_confirmation(user.wallet, org_connection_1.id, org.org_name, org_connection_1.invitation)
        sleep(1)

        # update connection status (org)
        org_connection_2 = check_connection_status(org.wallet, org_connection_1)

        return (org_connection_2, user_connection)

    def delete_user_and_org_wallets(self, user, org, raw_password):
        # cleanup after ourselves
        org_wallet_name = org.wallet.wallet_name
        res = delete_wallet(org_wallet_name, raw_password)
        self.assertEqual(res, 0)
        user_wallet_name = user.wallet.wallet_name
        res = delete_wallet(user_wallet_name, raw_password)
        self.assertEqual(res, 0)

    def schema_and_cred_def_for_org(self, org):
        # create a "dummy" schema/cred-def that is unique to this org (matches the Alice/Faber demo schema)
        wallet = org.wallet
        wallet_name = org.wallet.wallet_name

        (schema_json, creddef_template) = create_schema_json('schema_' + wallet_name, random_schema_version(), [
            'name', 'date', 'degree', 'age',
            ])
        schema = create_schema(wallet, schema_json, creddef_template)
        cred_def = create_creddef(wallet, schema, 'creddef_' + wallet_name, creddef_template)

         # Proof of Age
        proof_request = create_proof_request('Proof of Age Test', 'Proof of Age Test',
            [{'name':'name', 'restrictions':[{'issuer_did': '$ISSUER_DID'}]},
             {'name':'comments'}],
            [{'name': 'age','p_type': '>=','p_value': '$VALUE', 'restrictions':[{'issuer_did': '$ISSUER_DID'}]}]
            )

        return (schema, cred_def, proof_request)


    def issue_credential_from_org_to_user(self, org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag):
        # issue a credential based on the default schema/credential definition
        org_conversation_1 = send_credential_offer(org.wallet, org_connection,  
                                            cred_tag, schema_attrs, cred_def, 
                                            cred_name)
        sleep(2)

        i = 0
        while True:
            handled_count = handle_inbound_messages(user.wallet, user_connection)
            i = i + 1
            if handled_count > 0 or i > 3:
                break
            sleep(2)
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="CredentialOffer", status='Pending').all()
        user_conversation_1 = user_conversations[0]

        # send credential request (user -> org)
        user_conversation_2 = send_credential_request(user.wallet, user_connection, user_conversation_1)
        sleep(2)

        # send credential (org -> user)
        i = 0
        message = org_conversation_1
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.conversation_type == 'IssueCredential' or i > 3:
                break
            sleep(2)
        org_conversation_2 = message
        sleep(2)

        # accept credential and update status (user)
        i = 0
        message = user_conversation_2
        while True:
            message = poll_message_conversation(user.wallet, user_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        user_conversation_3 = message
        sleep(2)

        # update credential offer status (org)
        i = 0
        message = org_conversation_2
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        org_conversation_3 = message

    def issue_credential_from_org_to_user_bg_tasks(self, org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag):
        # issue a credential based on the default schema/credential definition
        org_conversation_1 = send_credential_offer(org.wallet, org_connection,  
                                            cred_tag, schema_attrs, cred_def, 
                                            cred_name)
        sleep(2)

        i = 0
        while True:
            handled_count = handle_inbound_messages(user.wallet, user_connection)
            i = i + 1
            if handled_count > 0 or i > 3:
                break
            sleep(2)
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="CredentialOffer", status='Pending').all()
        user_conversation_1 = user_conversations[0]

        # send credential request (user -> org)
        user_conversation_2 = send_credential_request(user.wallet, user_connection, user_conversation_1)
        sleep(2)

        # send credential (org -> user)
        i = 0
        message = org_conversation_1
        while True:
            poll_count = poll_message_conversations(org.wallet, org_connection)
            i = i + 1
            if poll_count == 1 or i > 3:
                break
            sleep(2)
        org_conversation_2 = AgentConversation.objects.filter(connection__wallet=org.wallet, id=message.id).all()[0]
        if org_conversation_2.conversation_type != 'IssueCredential':
            raise Exception("Expected IssueCredential but got " + org_conversation_2.conversation_type)
        sleep(2)

        # accept credential and update status (user)
        i = 0
        message = user_conversation_2
        while True:
            poll_count = poll_message_conversations(user.wallet, user_connection)
            i = i + 1
            if poll_count == 1 or i > 3:
                break
            sleep(2)
        user_conversation_3 = AgentConversation.objects.filter(connection__wallet=user.wallet, id=message.id).all()[0]
        if user_conversation_3.status != 'Accepted':
            raise Exception('Expected Accepted but got' + user_conversation_3.status)
        sleep(2)

        # update credential offer status (org)
        i = 0
        message = org_conversation_2
        while True:
            poll_count = poll_message_conversations(org.wallet, org_connection)
            i = i + 1
            if poll_count == 1 or i > 3:
                break
            sleep(2)
        org_conversation_3 = AgentConversation.objects.filter(connection__wallet=org.wallet, id=message.id).all()[0]
        if org_conversation_3.status != 'Accepted':
            raise Exception('Expected Accepted but got' + org_conversation_3.status)


    def test_register_org_with_schema_and_cred_def(self):
        # try creating a schema and credential definition under the organization
        (user, org, raw_password) = self.create_user_and_org()
        (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

        # fetch some stuff and validate some other stuff
        fetch_org = IndyOrganization.objects.filter(org_name=org.org_name).all()[0]
        self.assertEqual(len(fetch_org.wallet.indycreddef_set.all()), 1)
        fetch_creddef = fetch_org.wallet.indycreddef_set.all()[0]
        self.assertEqual(fetch_creddef.creddef_name, cred_def.creddef_name)

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_connection(self):
        # establish a connection between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

        (org_connection, user_connection) = self.establish_agent_connection(org, user)
        self.assertEqual(org_connection.status, 'Active')

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_credential_exchange(self):
        # exchange credentials between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

        # establish a connection
        (org_connection, user_connection) = self.establish_agent_connection(org, user)

        # issue credential offer (org -> user)
        schema_attrs = json.loads(cred_def.creddef_template)
        # data normally provided by the org data pipeline
        schema_attrs['name'] = 'Joe Smith'
        schema_attrs['date'] = '2018-01-01'
        schema_attrs['degree'] = 'B.A.Sc. Honours'
        schema_attrs['age'] = '25'
        org_conversation_1 = send_credential_offer(org.wallet, org_connection,  
                                            'Some Tag Value', schema_attrs, cred_def, 
                                            'Some Credential Name')
        sleep(2)

        # poll to receive credential offer
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="CredentialOffer", status='Pending').all()
        self.assertEqual(len(user_conversations), 0)
        user_credentials = list_wallet_credentials(user.wallet)
        self.assertEqual(len(user_credentials), 0)

        i = 0
        while True:
            handled_count = handle_inbound_messages(user.wallet, user_connection)
            i = i + 1
            if handled_count > 0 or i > 3:
                break
            sleep(2)
        self.assertEqual(handled_count, 1)
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="CredentialOffer", status='Pending').all()
        self.assertEqual(len(user_conversations), 1)
        user_conversation_1 = user_conversations[0]

        # send credential request (user -> org)
        user_conversation_2 = send_credential_request(user.wallet, user_connection, user_conversation_1)
        sleep(2)

        # send credential (org -> user)
        i = 0
        message = org_conversation_1
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.conversation_type == 'IssueCredential' or i > 3:
                break
            sleep(2)
        self.assertEqual(message.conversation_type, 'IssueCredential')
        org_conversation_2 = message
        sleep(2)

        # accept credential and update status (user)
        i = 0
        message = user_conversation_2
        while True:
            message = poll_message_conversation(user.wallet, user_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        self.assertEqual(message.status, 'Accepted')
        user_conversation_3 = message
        sleep(2)

        # update credential offer status (org)
        i = 0
        message = org_conversation_2
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        self.assertEqual(message.status, 'Accepted')
        org_conversation_3 = message

        # verify credential is in user wallet
        user_credentials = list_wallet_credentials(user.wallet)
        self.assertEqual(len(user_credentials), 1)

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_credential_exchange_bgtask(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

        # establish a connection
        (org_connection, user_connection) = self.establish_agent_connection(org, user)

        # make up a credential
        schema_attrs = json.loads(cred_def.creddef_template)
        schema_attrs['name'] = 'Joe Smith'
        schema_attrs['date'] = '2018-01-01'
        schema_attrs['degree'] = 'B.A.Sc. Honours'
        schema_attrs['age'] = '25'
        cred_name = 'Cred4Proof Credential Name'
        cred_tag = 'Cred4Proof Tag Value'

        # issue credential (org -> user)
        self.issue_credential_from_org_to_user_bg_tasks(org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag)

        # verify credential is in user wallet
        user_credentials = list_wallet_credentials(user.wallet)
        self.assertEqual(len(user_credentials), 1)

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_proof_exchange(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

        # establish a connection
        (org_connection, user_connection) = self.establish_agent_connection(org, user)

        # make up a credential
        schema_attrs = json.loads(cred_def.creddef_template)
        schema_attrs['name'] = 'Joe Smith'
        schema_attrs['date'] = '2018-01-01'
        schema_attrs['degree'] = 'B.A.Sc. Honours'
        schema_attrs['age'] = '25'
        cred_name = 'Cred4Proof Credential Name'
        cred_tag = 'Cred4Proof Tag Value'

        # issue credential (org -> user)
        self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag)

        # verify credential is in user wallet
        user_credentials = list_wallet_credentials(user.wallet)
        self.assertEqual(len(user_credentials), 1)

        # construct the proof request to send to the user (to whom we have just issued a credential)
        proof_req_attrs = proof_request.proof_req_attrs
        proof_req_predicates = proof_request.proof_req_predicates
        org_connection_data = json.loads(org_connection.connection_data)
        issuer_did = org_connection_data['data']['public_did']
        proof_req_attrs = proof_req_attrs.replace('$ISSUER_DID', issuer_did)
        proof_req_predicates = proof_req_predicates.replace('$ISSUER_DID', issuer_did)
        proof_req_predicates = proof_req_predicates.replace('"$VALUE"', '21')
        proof_req_attrs = json.loads(proof_req_attrs)
        proof_req_predicates = json.loads(proof_req_predicates)
        proof_name = "My Cool Proof"
        proof_uuid = "Some Uuid Value"

        # issue proof request (org -> user)
        org_conversation_1 = send_proof_request(org.wallet, org_connection, proof_uuid, proof_name, proof_req_attrs, proof_req_predicates)
        sleep(2)

        # poll to receive proof request
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="ProofRequest", status='Pending').all()
        self.assertEqual(len(user_conversations), 0)

        i = 0
        while True:
            handled_count = handle_inbound_messages(user.wallet, user_connection)
            i = i + 1
            if handled_count > 0 or i > 3:
                break
            sleep(2)
        self.assertEqual(handled_count, 1)
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="ProofRequest", status='Pending').all()
        self.assertEqual(len(user_conversations), 1)
        user_conversation_1 = user_conversations[0]

        # select credential(s) for proof (user)
        claim_data = get_claims_for_proof_request(user.wallet, user_connection, user_conversation_1)
        credential_attrs = {}
        for attr in claim_data['attrs']:
            # build array of credential id's (from wallet)
            claims = claim_data['attrs'][attr]
            if 0 < len(claims):
                self.assertEqual(len(claims), 1)
                credential_attrs[attr] = {'referent': claims[0]['cred_info']['referent']}
            else:
                # if no claim available, make up a self-attested value
                self.assertEqual(attr, 'comments')
                credential_attrs[attr] = {'value': 'user-supplied value'}

        # construct proof and send (user -> org)
        user_conversation_2 = send_claims_for_proof_request(user.wallet, user_connection, user_conversation_1, credential_attrs)

        # accept and validate proof (org)
        i = 0
        message = org_conversation_1
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        self.assertEqual(message.status, 'Accepted')
        self.assertEqual(message.proof_state, 'Verified')
        org_conversation_2 = message

        # TODO verify some stuff ...

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_proof_exchange_2_creds(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

        # establish a connection
        (org_connection, user_connection) = self.establish_agent_connection(org, user)

        # make up a credential
        schema_attrs = json.loads(cred_def.creddef_template)
        schema_attrs['name'] = 'Joe Smith'
        schema_attrs['date'] = '2018-01-01'
        schema_attrs['degree'] = 'B.A.Sc. Honours'
        schema_attrs['age'] = '25'
        cred_name = 'Cred4Proof Credential Name'
        cred_tag = 'Cred4Proof Tag Value'

        # issue credential (org -> user)
        self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag)

        # verify credential is in user wallet
        user_credentials = list_wallet_credentials(user.wallet)
        self.assertEqual(len(user_credentials), 1)

        # make up a credential
        schema_attrs = json.loads(cred_def.creddef_template)
        schema_attrs['name'] = 'Joe Smith 2'
        schema_attrs['date'] = '2018-01-02'
        schema_attrs['degree'] = 'M.Sc. Honours'
        schema_attrs['age'] = '28'
        cred_name = 'Cred4Proof Credential Name 2'
        cred_tag = 'Cred4Proof Tag Value 2'

        # issue credential (org -> user)
        self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag)

        # verify credential is in user wallet
        user_credentials = list_wallet_credentials(user.wallet)
        self.assertEqual(len(user_credentials), 2)

        # construct the proof request to send to the user (to whom we have just issued a credential)
        proof_req_attrs = proof_request.proof_req_attrs
        proof_req_predicates = proof_request.proof_req_predicates
        org_connection_data = json.loads(org_connection.connection_data)
        issuer_did = org_connection_data['data']['public_did']
        proof_req_attrs = proof_req_attrs.replace('$ISSUER_DID', issuer_did)
        proof_req_predicates = proof_req_predicates.replace('$ISSUER_DID', issuer_did)
        proof_req_predicates = proof_req_predicates.replace('"$VALUE"', '21')
        proof_req_attrs = json.loads(proof_req_attrs)
        proof_req_predicates = json.loads(proof_req_predicates)
        proof_name = "My Cool Proof"
        proof_uuid = "Some Uuid Value"

        # issue proof request (org -> user)
        org_conversation_1 = send_proof_request(org.wallet, org_connection, proof_uuid, proof_name, proof_req_attrs, proof_req_predicates)
        sleep(2)

        # poll to receive proof request
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="ProofRequest", status='Pending').all()
        self.assertEqual(len(user_conversations), 0)

        i = 0
        while True:
            handled_count = handle_inbound_messages(user.wallet, user_connection)
            i = i + 1
            if handled_count > 0 or i > 3:
                break
            sleep(2)
        self.assertEqual(handled_count, 1)
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="ProofRequest", status='Pending').all()
        self.assertEqual(len(user_conversations), 1)
        user_conversation_1 = user_conversations[0]

        # select credential(s) for proof (user) - there are 2 creds now
        claim_data = get_claims_for_proof_request(user.wallet, user_connection, user_conversation_1)
        for attr in claim_data['attrs']:
            # build array of credential id's (from wallet)
            claims = claim_data['attrs'][attr]
            if 0 < len(claims):
                self.assertEqual(len(claims), 2)
            else:
                self.assertEqual(attr, 'comments')

        # try again with additional_filters
        claim_data = get_claims_for_proof_request(user.wallet, user_connection, user_conversation_1, additional_filters={'degree':'M.Sc. Honours'})
        credential_attrs = {}
        for attr in claim_data['attrs']:
            # build array of credential id's (from wallet)
            claims = claim_data['attrs'][attr]
            if 0 < len(claims):
                self.assertEqual(len(claims), 1)
                credential_attrs[attr] = {'referent': claims[0]['cred_info']['referent']}
            else:
                # if no claim available, make up a self-attested value
                self.assertEqual(attr, 'comments')
                credential_attrs[attr] = {'value': 'user-supplied value'}

        # construct proof and send (user -> org)
        user_conversation_2 = send_claims_for_proof_request(user.wallet, user_connection, user_conversation_1, credential_attrs)

        # accept and validate proof (org)
        i = 0
        message = org_conversation_1
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        self.assertEqual(message.status, 'Accepted')
        self.assertEqual(message.proof_state, 'Verified')
        org_conversation_2 = message

        # TODO verify some stuff ...

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)

