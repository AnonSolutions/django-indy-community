from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import *


User = get_user_model()
TEST_USER_EMAIL = 'test@example.com'
TEST_USER_FIRST_NAME = 'Test'
TEST_USER_LAST_NAME = 'User'


class IndyWalletTests(TestCase):
    """
    Tests for Indy wallet model class
    """

    def test_wallet_create(self):
        # create a wallet
        my_wallet = IndyWallet.objects.create(
            wallet_name='test_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        my_wallet.save()

        fetch_wallet = IndyWallet.objects.filter(wallet_name='test_wallet').all()
        self.assertEqual(len(fetch_wallet), 1)
        self.assertEqual(fetch_wallet[0].wallet_name, 'test_wallet')


class IndyUserTests(TestCase):
    """
    Tests for Indy custom User class.
    """

    def setUp(self):
        # Creates a single-user test database.
        self.user = User.objects.create(
            email=TEST_USER_EMAIL,
            first_name=TEST_USER_FIRST_NAME,
            last_name=TEST_USER_LAST_NAME,
        )

    def test_user_exists(self):
        # Tests user in setUp() does exists
        my_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        self.assertEqual(my_user.first_name, TEST_USER_FIRST_NAME)

    def test_user_with_wallet(self):
        # test we can create a user with a wallet
        my_wallet = IndyWallet.objects.create(
            wallet_name='test_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        my_wallet.save()
        my_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        my_user.wallet = my_wallet
        my_user.save()

        fetch_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        self.assertEqual(my_user.wallet.wallet_name, my_wallet.wallet_name)


class IndyOrganizationTests(TestCase):
    """
    Tests for Indy organization class 
    """

    def test_organization_create(self):
        # tests creating an organization with a wallet 
        my_wallet = IndyWallet.objects.create(
            wallet_name='test_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        my_wallet.save()
        my_org = IndyOrganization.objects.create(
            org_name='My Org',
            wallet=my_wallet,
        )
        my_org.save()

        fetch_org = IndyOrganization.objects.filter(org_name='My Org').all()
        self.assertEqual(len(fetch_org), 1)
        self.assertEqual(fetch_org[0].wallet.wallet_name, 'test_wallet')


class IndyOrgRelationshipTests(TestCase):
    """
    Tests for Indy organization/user relationship class 
    """

    def test_relationship_create(self):
        # tests creating a relationship between a user and organization
        user_wallet = IndyWallet.objects.create(
            wallet_name='user_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        user_wallet.save()
        my_user = User.objects.create(
            email='user@org.com',
            first_name='org',
            last_name='user',
            wallet=user_wallet,
        )
        org_wallet = IndyWallet.objects.create(
            wallet_name='org_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        org_wallet.save()
        my_org = IndyOrganization.objects.create(
            org_name='My Org',
            wallet=org_wallet,
        )
        my_org.save()
        my_relationship = IndyOrgRelationship.objects.create(
            org=my_org,
            user=my_user,
        )

        fetch_user = User.objects.filter(email='user@org.com').all()[0]
        self.assertEqual(len(fetch_user.indyrelationship_set.all()), 1)
        user_org = fetch_user.indyrelationship_set.all()[0].org
        self.assertEqual(user_org.org_name, 'My Org')

        fetch_org = IndyOrganization.objects.filter(org_name='My Org').all()[0]
        self.assertEqual(len(fetch_org.indyrelationship_set.all()), 1)
        org_user = fetch_org.indyrelationship_set.all()[0].user
        self.assertEqual(org_user.email, 'user@org.com')


class IndySchemaTests(TestCase):
    """
    Tests for IndySchema class
    """
    def test_schema_create(self):
        schema = IndySchema.objects.create(
            ledger_schema_id='123',
            schema_name='My Schema',
            schema_version='1.1.1',
            schema='this is the schema data',
            schema_template='template for adding credentials',
            schema_data='data written to the ledger',
        )
        schema.save()

        fetch_schema = IndySchema.objects.filter(ledger_schema_id='123').all()
        self.assertEqual(len(fetch_schema), 1)
        self.assertEqual(fetch_schema[0].schema_name, 'My Schema')


class IndyCredentialDefinitionTests(TestCase):
    """
    Tests for IndyCredentialDefinition class
    """
    def test_credentialdefinition_create(self):
        wallet = IndyWallet.objects.create(
            wallet_name='test_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        wallet.save()
        schema = IndySchema.objects.create(
            ledger_schema_id='123',
            schema_name='My Schema',
            schema_version='1.1.1',
            schema='this is the schema data',
            schema_template='template for adding credentials',
            schema_data='data written to the ledger',
        )
        schema.save()
        cred_def = IndyCredentialDefinition.objects.create(
            ledger_creddef_id='456',
            ledger_schema=schema,
            wallet=wallet,
            creddef_name='my cred def',
            creddef_handle='4',
            creddef_template='a template for adding credentials',
            creddef_data='data written to the ledger',
        )
        cred_def.save()

        fetch_cred_def = IndyCredentialDefinition.objects.filter(ledger_creddef_id='456').all()
        self.assertEqual(len(fetch_cred_def), 1)
        self.assertEqual(fetch_cred_def[0].ledger_schema.schema_name, 'My Schema')
        self.assertEqual(fetch_cred_def[0].creddef_name, 'my cred def')


class IndyProofRequestTests(TestCase):
    """
    Tests for IndyProofRequest class
    """
    def test_proofrequest_create(self):
        proof_request = IndyProofRequest.objects.create(
            proof_req_name='test name',
            proof_req_description='a description',
            proof_req_attrs='revealed attributes',
            proof_req_predicates='zkp attributes',
        )
        proof_request.save()

        fetch_proof_request = IndyProofRequest.objects.filter(proof_req_name='test name').all()
        self.assertEqual(len(fetch_proof_request), 1)
        self.assertEqual(fetch_proof_request[0].proof_req_name, 'test name')


class AgentConnectionTests(TestCase):
    """
    Tests for Indy AgentConnection class
    """
    def test_connection_create(self):
        wallet = IndyWallet.objects.create(
            wallet_name='test_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        wallet.save()
        connection = AgentConnection.objects.create(
            wallet=wallet,
            partner_name='partner',
            invitation='invitation to connect',
            token='token to identify connection',
            status='Active',
            connection_type='In or Out',
            connection_data='data representing connection state',
        )
        connection.save()

        fetch_connection = AgentConnection.objects.filter(wallet=wallet, partner_name='partner').all()
        self.assertEqual(len(fetch_connection), 1)
        self.assertEqual(fetch_connection[0].partner_name, 'partner')


class AgentConversationTests(TestCase):
    """
    Tests for Indy AgentConversation class
    """
    def test_conversation_create(self):
        wallet = IndyWallet.objects.create(
            wallet_name='test_wallet',
            wallet_config='{"some":"test", "string":"."}',
        )
        wallet.save()
        connection = AgentConnection.objects.create(
            wallet=wallet,
            partner_name='partner',
            invitation='invitation to connect',
            token='token to identify connection',
            status='Active',
            connection_type='In or Out',
            connection_data='data representing connection state',
        )
        connection.save()
        conversation = AgentConversation.objects.create(
            connection=connection,
            conversation_type='proof or credential',
            message_id='123',
            status='Active',
            proof_state='only for proofs',
            conversation_data='data representing conversation state',
        )
        conversation.save()

        fetch_conversation = AgentConversation.objects.filter(connection__wallet=wallet, connection=connection, message_id='123').all()
        self.assertEqual(len(fetch_conversation), 1)
        self.assertEqual(fetch_conversation[0].conversation_data, 'data representing conversation state')

