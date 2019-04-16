from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

import json

from .models import *


###############################################################
# Forms to support user and organization registration
###############################################################

class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=80, required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=150, required=False,
                                help_text='Optional.')
    email = forms.EmailField(
        max_length=254, help_text='Required. Provide a valid email address.')

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


class OrganizationSignUpForm(UserSignUpForm):
    org_name = forms.CharField(max_length=60, required=True,
                                 help_text='Required.')
    org_role_name = forms.CharField(max_length=40, required=True,
                                 help_text='Required.')


######################################################################
# forms to create and confirm agent-to-agent connections
######################################################################
class WalletNameForm(forms.Form):
    wallet_name = forms.CharField(label='Wallet Name', max_length=60)

    def __init__(self, *args, **kwargs):
        super(WalletNameForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True


class SendConnectionInvitationForm(WalletNameForm):
    partner_name = forms.CharField(label='Partner Name', max_length=60)

    def __init__(self, *args, **kwargs):
        super(SendConnectionInvitationForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True


class SendConnectionResponseForm(SendConnectionInvitationForm):
    connection_id = forms.IntegerField(label="Id")
    invitation_details = forms.CharField(label='Invitation', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendConnectionResponseForm, self).__init__(*args, **kwargs)
        self.fields['connection_id'].widget.attrs['readonly'] = True
        #self.fields['invitation_details'].widget.attrs['readonly'] = True


class PollConnectionStatusForm(WalletNameForm):
    connection_id = forms.IntegerField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConnectionStatusForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True


######################################################################
# forms to offer, request, send and receive credentials
######################################################################
class SendConversationResponseForm(WalletNameForm):
    conversation_id = forms.IntegerField(label="Id")

    def __init__(self, *args, **kwargs):
        super(SendConversationResponseForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True


class PollConversationStatusForm(WalletNameForm):
    conversation_id = forms.IntegerField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConversationStatusForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        selffields['conversation_id'].widget.attrs['readonly'] = True


class SelectCredentialOfferForm(WalletNameForm):
    connection_id = forms.IntegerField(label="Connection Id")
    cred_def = forms.ModelChoiceField(label='Cred Def', queryset=IndyCredentialDefinition.objects.all())

    def __init__(self, *args, **kwargs):
        super(SelectCredentialOfferForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        initial = kwargs.get('initial')
        if initial:
            wallet_name = initial.get('wallet_name')
            self.fields['cred_def'].queryset = IndyCredentialDefinition.objects.filter(wallet__wallet_name=wallet_name).all()


class SendCredentialOfferForm(WalletNameForm):
    connection_id = forms.IntegerField(label="Connection Id")
    credential_tag = forms.CharField(label='Credential Tag', max_length=80)
    credential_name = forms.CharField(label='Credential Name', max_length=80)
    cred_def = forms.CharField(label='Cred Def', max_length=80)
    schema_attrs = forms.CharField(label='Credential Attrs', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialOfferForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['cred_def'].widget.attrs['readonly'] = True


class SendCredentialResponseForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    from_partner_name = forms.CharField(label='Partner Name', max_length=60)
    claim_id = forms.CharField(label='Credential Id', max_length=80)
    claim_name = forms.CharField(label='Credential Name', max_length=80)
    credential_attrs = forms.CharField(label='Credential Attrs', max_length=4000, widget=forms.Textarea)
    libindy_offer_schema_id = forms.CharField(label='Schema Id', max_length=120, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialResponseForm, self).__init__(*args, **kwargs)
        self.fields['from_partner_name'].widget.attrs['readonly'] = True
        self.fields['claim_id'].widget.attrs['readonly'] = True
        self.fields['claim_name'].widget.attrs['readonly'] = True
        self.fields['credential_attrs'].widget.attrs['readonly'] = True
        self.fields['libindy_offer_schema_id'].widget.attrs['readonly'] = True


######################################################################
# forms to request, send and receive proofs
######################################################################
class SelectProofRequestForm(WalletNameForm):
    connection_id = forms.IntegerField(label="Connection Id")
    proof_request = forms.ModelChoiceField(label='Proof Request Type', queryset=IndyProofRequest.objects.all())

    def __init__(self, *args, **kwargs):
        super(SelectProofRequestForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True


class SendProofRequestForm(WalletNameForm):
    connection_id = forms.IntegerField(label="Connection Id")
    proof_name = forms.CharField(label='Proof Name', max_length=400)
    proof_uuid = forms.CharField(label='Proof UUID', max_length=60)
    proof_attrs = forms.CharField(label='Proof Attributes', max_length=4000, widget=forms.Textarea)
    proof_predicates = forms.CharField(label='Proof Predicates', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendProofRequestForm, self).__init__(*args, **kwargs)
        self.fields['wallet_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True


class SendProofReqResponseForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    from_partner_name = forms.CharField(label='Partner Name', max_length=60)
    proof_req_name = forms.CharField(label='Proof Request Name', max_length=400)
    # TODO not sure if this element is required on this form ...
    requested_attrs = forms.CharField(label='Requested Attrs', widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(SendProofReqResponseForm, self).__init__(*args, **kwargs)
        self.fields['from_partner_name'].widget.attrs['readonly'] = True
        self.fields['proof_req_name'].widget.attrs['readonly'] = True
        # TODO not sure if this element is required on this form ...
        self.fields['requested_attrs'].widget.attrs['readonly'] = True


class SelectProofReqClaimsForm(SendProofReqResponseForm):
    # TODO maybe move requested_attrs to this form (?)

    def __init__(self, *args, **kwargs):
        super(SelectProofReqClaimsForm, self).__init__(*args, **kwargs)
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

