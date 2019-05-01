from django.conf import settings
from django.db import models
from django.contrib.sessions.models import Session
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, PermissionsMixin

from django.utils import timezone

from datetime import datetime, date, timedelta
import json


USER_ROLES = (
    'Admin',
    'User',
)

# base class for Indy wallets
class IndyWallet(models.Model):
    wallet_name = models.CharField(max_length=60, unique=True)
    wallet_config = models.TextField(max_length=4000, blank=True)

    def __str__(self):
        return self.wallet_name

# special class for managing Indy users and wallets
class IndyUserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save()

        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

# special class for Indy users (owns a wallet)
class IndyUser(AbstractBaseUser, PermissionsMixin):
    """
    Simple custom User class with email-based login.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into this admin site."
    )
    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        )
    )
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    wallet = models.ForeignKey(IndyWallet, to_field="wallet_name", related_name='wallet_user', blank = True, null=True, on_delete=models.CASCADE)
    managed_wallet = models.BooleanField(default=True)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    objects = IndyUserManager()

    @property
    def roles(self):
        # -> Iterable
        # Produce a list of the given user's roles.

        return filter(self.has_role, USER_ROLES)

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def add_role(self, role):
        # String ->
        # Adds user to role group

        self.groups.add(Group.objects.get(name=role))

    def has_role(self, role):
        # String -> Boolean
        # Produce true if user is in the given role group.

        return self.groups.filter(name=role).exists()


# Roles to which an organization can belong
class IndyOrgRole(models.Model):
    name = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.name

# Base class for organizations that use the Indy platform
class IndyOrganization(models.Model):
    org_name = models.CharField(max_length=60, unique=True)
    wallet = models.ForeignKey(IndyWallet, to_field="wallet_name", related_name='wallet_org', blank = True, null=True, on_delete=models.CASCADE)
    role = models.ForeignKey(IndyOrgRole, blank = True, null=True, on_delete=models.CASCADE)
    ico_url = models.CharField(max_length=120, blank = True, null=True)
    managed_wallet = models.BooleanField(default=True)

    def __str__(self):
        return self.org_name

# Association class for user/organization relationship
class IndyOrgRelationship(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='indyrelationship_set', on_delete=models.CASCADE)
    org = models.ForeignKey(IndyOrganization, related_name='indyrelationship_set', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email + ':' + self.org.org_name

# track user session and attached wallet for background agents
class IndySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    wallet_name = models.CharField(max_length=60, blank=True, null=True)


# reference to a schema on the ledger
class IndySchema(models.Model):
    ledger_schema_id = models.CharField(max_length=80, unique=True)
    schema_name = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=80)
    schema = models.TextField(max_length=4000)
    schema_template = models.TextField(max_length=4000)
    schema_data = models.TextField(max_length=4000)
    # orgs which contain these role(s) will automatically get cred defs created for this schema
    roles = models.ManyToManyField(IndyOrgRole)

    def __str__(self):
        return self.schema_name


# reference to a credential definition on the ledger
class IndyCredentialDefinition(models.Model):
    ledger_creddef_id = models.CharField(max_length=80, unique=True)
    ledger_schema = models.ForeignKey(IndySchema, on_delete=models.CASCADE)
    wallet = models.ForeignKey(IndyWallet, to_field="wallet_name", related_name='indycreddef_set', on_delete=models.CASCADE)
    creddef_name = models.CharField(max_length=80)
    creddef_handle = models.CharField(max_length=80)
    creddef_template = models.TextField(max_length=4000)
    creddef_data = models.TextField(max_length=4000)

    def __str__(self):
        return self.ledger_schema.schema_name + ":" + self.wallet.wallet_name + ":" + self.creddef_name


# Description of a proof request
class IndyProofRequest(models.Model):
    proof_req_name = models.CharField(max_length=400, unique=True)
    proof_req_description = models.TextField(max_length=4000)
    proof_req_attrs = models.TextField(max_length=4000)
    proof_req_predicates = models.TextField(max_length=4000, blank=True)

    def __str__(self):
        return self.proof_req_name


# base class for Agent connections
class AgentConnection(models.Model):
    wallet = models.ForeignKey(IndyWallet, to_field="wallet_name", on_delete=models.CASCADE)
    partner_name = models.CharField(max_length=60)
    invitation = models.TextField(max_length=4000, blank=True)
    token = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20)
    connection_type = models.CharField(max_length=20)
    connection_data = models.TextField(max_length=4000, blank=True)

    def __str__(self):
        return self.wallet.wallet_name + ":" + self.partner_name + ", " +  self.status

    # script from @burdettadam, map to the invite format expected by Connect.Me
    def invitation_shortform(self, source_name, target_name, institution_logo_url):
        invite = json.loads(self.invitation)
        cm_invite = { "id": invite["connReqId"],
                "s" :{"d" :invite["senderDetail"]["DID"],
                        "dp":{"d":invite["senderDetail"]["agentKeyDlgProof"]["agentDID"],
                              "k":invite["senderDetail"]["agentKeyDlgProof"]["agentDelegatedKey"],
                              "s":invite["senderDetail"]["agentKeyDlgProof"]["signature"]
                            },
                        "l" :invite["senderDetail"]["logoUrl"],
                        "n" :invite["senderDetail"]["name"],
                        "v" :invite["senderDetail"]["verKey"]
                        },
                "sa":{"d":invite["senderAgencyDetail"]["DID"],
                        "e":invite["senderAgencyDetail"]["endpoint"],
                        "v":invite["senderAgencyDetail"]["verKey"]
                    },
                "sc":invite["statusCode"],
                "sm":invite["statusMsg"],
                "t" :invite["targetName"]
                }
        cm_invite["s"]["n"] = source_name
        cm_invite["t"] = target_name
        cm_invite["s"]["l"] = institution_logo_url
        return json.dumps(cm_invite)


# base class for Agent conversations - issue/receive credential and request/provide proof
class AgentConversation(models.Model):
    connection = models.ForeignKey(AgentConnection, on_delete=models.CASCADE)
    conversation_type = models.CharField(max_length=30)
    message_id = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    proof_state = models.CharField(max_length=20, blank=True)
    conversation_data = models.TextField(max_length=4000, blank=True)

    def __str__(self):
        return self.connection.wallet.wallet_name + ":" + self.connection.partner_name + ":" + self.message_id + ", " +  self.conversation_type + " " + self.status
