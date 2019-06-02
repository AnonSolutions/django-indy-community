from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db.models import Q

import json

from .models import *


###############################################################
# Forms to request a connection to a mobile wallet (user only)
###############################################################
class RequestMobileConnectionForm(UserCreationForm):
    email = forms.CharField(label='Email', max_length=120)
    org = forms.ModelChoiceField(label='Organization', queryset=IndyOrganization.objects.filter(Q(role__name='School') | Q(role__name='Employer') | Q(role__name='Bank') | Q(role__name='Goverment')).all())

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'org')


###############################################################
# Forms to support user and organization registration
###############################################################
class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=80, label='First Name', required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=150, label='Last Name', required=False,
                                 help_text='Optional.')
    email = forms.EmailField(max_length=254, label='Email Address', required=True,
                                 help_text='Required. Provide a valid email address.')

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


class OrganizationSignUpForm(UserSignUpForm):
    org_name = forms.CharField(max_length=60, label='Company Name', required=True,
                                 help_text='Required.')
    org_role_name = forms.CharField(max_length=40, label='Company Role', required=True,
                                 help_text='Required.')
    ico_url = forms.CharField(max_length=120, label="URL for company logo", required=False)


######################################################################
# forms to create and confirm agent-to-agent connections
######################################################################
class WalletNameForm(forms.Form):
    wallet_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(WalletNameForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True

class VisibleWalletNameForm(forms.Form):
    wallet_name = forms.CharField(max_length=60)

    def __init__(self, *args, **kwargs):
        super(VisibleWalletNameForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True


class SendConnectionInvitationForm(WalletNameForm):
    partner_name = forms.CharField(label='Partner Name', max_length=60)

    def __init__(self, *args, **kwargs):
        super(SendConnectionInvitationForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['wallet_name'].widget.attrs['hidden'] = True


class SendConnectionResponseForm(SendConnectionInvitationForm):
    connection_id = forms.IntegerField(widget=forms.HiddenInput())
    invitation_details = forms.CharField(label='Invitation', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendConnectionResponseForm, self).__init__(*args, **kwargs)
        self.fields['connection_id'].widget.attrs['readonly'] = True


class PollConnectionStatusForm(VisibleWalletNameForm):
    connection_id = forms.IntegerField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConnectionStatusForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True


######################################################################
# forms to offer, request, send and receive credentials
######################################################################
class SendConversationResponseForm(WalletNameForm):
    conversation_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(SendConversationResponseForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['wallet_name'].widget.attrs['hidden'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True


class PollConversationStatusForm(VisibleWalletNameForm):
    conversation_id = forms.IntegerField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConversationStatusForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True


class SelectCredentialOfferForm(WalletNameForm):
    connection_id = forms.IntegerField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label='Partner Name', max_length=60)
    cred_def = forms.ModelChoiceField(label='Cred Def', queryset=IndyCredentialDefinition.objects.all())

    def __init__(self, *args, **kwargs):
        super(SelectCredentialOfferForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['wallet_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True

        # build a list of Credential Definitions available to the current wallet
        initial = kwargs.get('initial')
        if initial:
            wallet_name = initial.get('wallet_name')
            self.fields['cred_def'].queryset = IndyCredentialDefinition.objects.filter(wallet__wallet_name=wallet_name).all()


class SendCredentialOfferForm(WalletNameForm):
    connection_id = forms.IntegerField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label='Partner Name', max_length=60)
    cred_def = forms.CharField(max_length=80, widget=forms.HiddenInput())
    credential_name = forms.CharField(label='Credential Name', max_length=80)
    credential_tag = forms.CharField(max_length=80, widget=forms.HiddenInput())
    schema_attrs = forms.CharField(label='Credential Attributes', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialOfferForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['wallet_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True
        self.fields['cred_def'].widget.attrs['readonly'] = True

        # build a list of attributes for the given schema
        initial = kwargs.get('initial')
        if initial:
            schema_attrs = initial.get('schema_attrs', '{}')
            schema_attrs = json.loads(schema_attrs)
            self.fields['schema_attrs'].widget.attrs['hidden'] = True
            for attr in schema_attrs:
                field_name = 'schema_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, max_length=200)


class SendCredentialResponseForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    from_partner_name = forms.CharField(label='Partner Name', max_length=60)
    claim_id = forms.CharField(max_length=80, widget=forms.HiddenInput())
    claim_name = forms.CharField(label='Credential Name', max_length=400)
    libindy_offer_schema_id = forms.CharField(max_length=120, widget=forms.HiddenInput())
    credential_attrs = forms.CharField(label='Credential Attrs', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialResponseForm, self).__init__(*args, **kwargs)
        self.fields['from_partner_name'].widget.attrs['readonly'] = True
        self.fields['claim_id'].widget.attrs['readonly'] = True
        self.fields['claim_name'].widget.attrs['readonly'] = True
        self.fields['libindy_offer_schema_id'].widget.attrs['readonly'] = True
        self.fields['credential_attrs'].widget.attrs['readonly'] = True

        # build a list of attributes for the current schema
        initial = kwargs.get('initial')
        if initial:
            credential_attrs = initial.get('credential_attrs', {})
            self.fields['credential_attrs'].widget.attrs['hidden'] = True
            for attr in credential_attrs:
                field_name = 'credential_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, initial=credential_attrs[attr])
                self.fields[field_name].widget.attrs['readonly'] = True


######################################################################
# forms to request, send and receive proofs
######################################################################
class SelectProofRequestForm(WalletNameForm):
    connection_id = forms.IntegerField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label='Partner Name', max_length=60)
    proof_request = forms.ModelChoiceField(label='Proof Request Type', queryset=IndyProofRequest.objects.all())

    def __init__(self, *args, **kwargs):
        super(SelectProofRequestForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['wallet_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True


class SendProofRequestForm(WalletNameForm):
    connection_id = forms.IntegerField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label='Partner Name', max_length=60)
    proof_name = forms.CharField(label='Proof Name', max_length=400)
    proof_attrs = forms.CharField(label='Proof Attributes', max_length=4000, widget=forms.Textarea)
    proof_predicates = forms.CharField(label='Proof Predicates', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendProofRequestForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['wallet_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True


class SendProofReqResponseForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    from_partner_name = forms.CharField(label='Partner Name', max_length=60)
    proof_req_name = forms.CharField(label='Proof Request Name', max_length=400)

    def __init__(self, *args, **kwargs):
        super(SendProofReqResponseForm, self).__init__(*args, **kwargs)
        self.fields['from_partner_name'].widget.attrs['readonly'] = True
        self.fields['proof_req_name'].widget.attrs['readonly'] = True


class SelectProofReqClaimsForm(SendProofReqResponseForm):
    requested_attrs = forms.CharField(label='Requested Attrs', widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(SelectProofReqClaimsForm, self).__init__(*args, **kwargs)

        # list requested attributes and the available claims, for the user to select
        initial = kwargs.get('initial')
        if initial:
            field_attrs = initial.get('requested_attrs', '{}')
            if 'attrs' in field_attrs:
                for attr in field_attrs['attrs']:
                    field_name = 'proof_req_attr_' + attr
                    choices = []
                    claim_no = 0
                    if 0 < len(field_attrs['attrs'][attr]):
                        for claim in field_attrs['attrs'][attr]:
                            choices.append(('ref::'+claim['cred_info']['referent'], json.dumps(claim['cred_info']['attrs'])))
                            claim_no = claim_no + 1
                        self.fields[field_name] = forms.ChoiceField(label='Select claim for '+attr, choices=tuple(choices), widget=forms.RadioSelect())
                    else:
                        self.fields[field_name] = forms.CharField(label='No claims available for '+attr+', enter value:', max_length=80)

