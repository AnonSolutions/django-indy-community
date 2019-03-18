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
        config = wallet.wallet_config

        (schema_json, creddef_template) = create_schema_json('schema_' + wallet_name, random_schema_version(), [
            'name', 'date', 'degree', 'age',
            ])
        schema = create_schema(wallet, json.loads(config), schema_json, creddef_template)
        creddef = create_creddef(wallet, json.loads(config), schema, 'creddef_' + wallet_name, creddef_template)

         # Proof of Age
        proof_request = create_proof_request('Proof of Age Test', 'Proof of Age Test',
            [{'name':'name', 'restrictions':[{'issuer_did': '$ISSUER_DID'}]}],
            [{'name': 'age','p_type': '>=','p_value': '$VALUE', 'restrictions':[{'issuer_did': '$ISSUER_DID'}]}]
            )

        return (schema, creddef, proof_request)


    def test_register_org_with_schema_and_cred_def(self):
        # try creating a schema and credential definition under the organization
        (user, org, raw_password) = self.create_user_and_org()
        (schema, creddef, proof_request) = self.schema_and_cred_def_for_org(org)

        # fetch some stuff and validate some other stuff
        fetch_org = IndyOrganization.objects.filter(org_name=org.org_name).all()[0]
        self.assertEqual(len(fetch_org.wallet.indycreddef_set.all()), 1)
        fetch_creddef = fetch_org.wallet.indycreddef_set.all()[0]
        self.assertEqual(fetch_creddef.creddef_name, creddef.creddef_name)

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_connection(self):
        # establish a connection between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, creddef, proof_request) = self.schema_and_cred_def_for_org(org)

        # send connection request (org -> user)
        org_config = json.loads(org.wallet.wallet_config)
        (org_connection_data_1, invite_details) = send_connection_invitation(org.wallet, org_config, user.email)
        sleep(1)

        # accept connection request (user -> org)
        user_config = json.loads(user.wallet.wallet_config)
        user_connection_data = send_connection_confirmation(user.wallet, user_config, org.org_name, invite_details)
        sleep(1)

        # update connection status (org)
        (org_connection_data_2, return_state) = check_connection_status(org.wallet, org_config, user.email, org_connection_data_1)
        self.assertEqual(return_state, 'Active')

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_credential_exchange(self):
        # exchange credentials between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, creddef, proof_request) = self.schema_and_cred_def_for_org(org)

        # TODO establish a connection

        # TODO issue credential offer (org -> user)

        # TODO send credential request (user -> org)

        # TODO send credential (org -> user)

        # TODO accept credential and update status (user)

        # TODO update credential offer status (user)

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)


    def test_agent_proof_exchange(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()
        (schema, creddef, proof_request) = self.schema_and_cred_def_for_org(org)

        # TODO issue credential (org -> user)

        # TODO issue proof request (org -> user)

        # TODO accept proof request (user)

        # TODO select credential(s) for proof (user)

        # TODO construct proof and send (user -> org)

        # TODO accept and validate proof (org)

        # clean up after ourself
        self.delete_user_and_org_wallets(user, org, raw_password)

