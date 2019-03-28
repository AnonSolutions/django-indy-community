from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login
from django.urls import reverse

from .forms import *
from .models import *
from .wallet_utils import *
from .registration_utils import *
from .agent_utils import *
from .signals import handle_wallet_login_internal, namespaced_template


###############################################################
# UI views to support user and organization registration
###############################################################
# Sign up as a site user, and create a wallet
def user_signup_view(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            if Group.objects.filter(name='User').exists():
                user.groups.add(Group.objects.get(name='User'))
            user.save()

            # create an Indy wallet - derive wallet name from email, and re-use raw password
            user = user_provision(user, raw_password)

            # TODO need to auto-login with Atria custom user
            #login(request, user)

            return redirect('login')
    else:
        form = UserSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


# Sign up as an org user, and create a wallet
def org_signup_view(request):
    if request.method == 'POST':
        form = OrganizationSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            if Group.objects.filter(name='Admin').exists():
                user.groups.add(Group.objects.get(name='Admin'))
            user.save()

            # create and provision org, including org wallet
            org_name = form.cleaned_data.get('org_name')
            org_role_name = form.cleaned_data.get('org_role_name')
            org_role, created = IndyOrgRole.objects.get_or_create(name=org_role_name)
            org = org_signup(user, raw_password, org_name, org_role)

            # TODO need to auto-login with Atria custom user
            #login(request, user)

            return redirect('login')
    else:
        form = OrganizationSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


###############################################################
# UI views to support Django wallet login/logoff
###############################################################
def handle_wallet_login(request):
    if request.method=='POST':
        form = WalletLoginForm(request.POST)
        if form.is_valid():
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            #now in the object cd, you have the form as a dictionary.
            wallet_name = cd.get('wallet_name')
            raw_password = cd.get('raw_password')

            try:
                wallet_handle = handle_wallet_login_internal(request, wallet_name, raw_password)

                print(" >>> Opened wallet for", wallet_name, wallet_handle)
                return render(request, 'indy/form_response.html', {'msg': 'Opened wallet for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to open wallet for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to open wallet for ' + wallet_name})

    else:
        form = WalletLoginForm()

    return render(request, 'indy/wallet_login.html', {'form': form})


def handle_wallet_logout(request):
    indy_wallet_logout(None, request.user, request)
    return render(request, 'indy/form_response.html', {'msg': 'Logged out of wallet(s)'})


###############################################################
# UI views to support wallet and agent UI functions
###############################################################
def individual_profile_view(request):
    return render(request, 'indy/individual_profile.html')

def individual_wallet_view(request):
    return render(request, 'indy/individual_wallet.html')

#def individual_connections_view(request):
#    return render(request, 'indy/individual_connections.html')

def individual_conversations_view(request):
    return render(request, 'indy/individual_conversations.html')

def individual_credentials_view(request):
    return render(request, 'indy/individual_credentials.html')

def organization_profile_view(request):
    return render(request, 'indy/organization_profile.html')

def organization_data_view(request):
    return render(request, 'indy/organization_data.html')

def organization_wallet_view(request):
    return render(request, 'indy/organization_wallet.html')

#def organization_connections_view(request):
#    return render(request, 'indy/organization_connections.html')

def organization_conversations_view(request):
    return render(request, 'indy/organization_conversations.html')

def organization_credentials_view(request):
    return render(request, 'indy/organization_credentials.html')


######################################################################
# views to create and confirm agent-to-agent connections
######################################################################
def list_connections(request):
    # expects a wallet to be opened in the current session
    wallet_name = request.session['wallet_name']
    connections = AgentConnection.objects.filter(wallet__wallet_name=wallet_name).all()
    return render(request, namespaced_template(request, 'connection/list.html'), {'wallet_name': wallet_name, 'connections': connections})


def handle_connection_request(request):
    if request.method=='POST':
        form = SendConnectionInvitationForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            cd = form.cleaned_data
            partner_name = cd.get('partner_name')

            # get user or org associated with this wallet
            wallet_name = request.session['wallet_name']
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()
            wallet_type = request.session['wallet_type']
            wallet_owner = request.session['wallet_owner']

            # get user or org associated with target partner
            target_user = IndyUser.objects.filter(email=partner_name).all()
            target_org = IndyOrganization.objects.filter(org_name=partner_name).all()

            if 0 < len(target_user):
                their_wallet = target_user[0].wallet
            elif 0 < len(target_org):
                their_wallet = target_org[0].wallet
            else:
                their_wallet = None

            # set wallet password
            # TODO vcx_config['something'] = raw_password

            # build the connection and get the invitation data back
            try:
                my_connection = send_connection_invitation(wallet, partner_name)

                if their_wallet is not None:
                    their_connection = AgentConnection(
                        wallet = their_wallet,
                        partner_name = wallet_owner,
                        invitation = my_connection.invitation,
                        connection_type = 'Inbound',
                        status = 'Pending')
                    their_connection.save()

                return render(request, 'indy/form_response.html', {'msg': 'Updated connection for ' + wallet.wallet_name, 'msg_txt': my_connection.invitation, 'msg_txt2': my_connection.token })
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to create request for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to create request for ' + wallet_name})

    else:
        if 'wallet_name' in request.session:
            wallet_name = request.session['wallet_name']
        else:
            wallet_name = ''
        form = SendConnectionInvitationForm(initial={'wallet_name': wallet_name})

        return render(request, 'indy/connection/request.html', {'form': form})
    

def handle_connection_response(request):
    if request.method=='POST':
        form = SendConnectionResponseForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            cd = form.cleaned_data
            connection_id = cd.get('connection_id')
            partner_name = cd.get('partner_name')
            invitation_details = cd.get('invitation_details')

            # get user or org associated with this wallet
            wallet_name = request.session['wallet_name']
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()
            wallet_type = request.session['wallet_type']
            wallet_owner = request.session['wallet_owner']

            # set wallet password
            # TODO vcx_config['something'] = raw_password

            # build the connection and get the invitation data back
            try:
                my_connection = send_connection_confirmation(wallet, partner_name, invitation_details)

                return render(request, 'indy/form_response.html', {'msg': 'Updated connection for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to update request for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to update request for ' + wallet_name})

    else:
        # find connection request
        wallet_name = request.session['wallet_name']
        connection_id = request.GET.get('id', None)
        connections = []
        if connection_id:
            connections = AgentConnection.objects.filter(id=connection_id, wallet__wallet_name=wallet_name).all()
        if len(connections) > 0:
            form = SendConnectionResponseForm(initial={ 'connection_id': connection_id,
                                                        'wallet_name': connections[0].wallet.wallet_name, 
                                                        'partner_name': connections[0].partner_name, 
                                                        'invitation_details': connections[0].invitation })
        else:
            wallet_name = request.session['wallet_name']
            form = SendConnectionResponseForm(initial={'connection_id': 0, 'wallet_name': wallet_name})

    return render(request, 'indy/connection/response.html', {'form': form})
    

def poll_connection_status(request):
    if request.method=='POST':
        form = PollConnectionStatusForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            cd = form.cleaned_data
            connection_id = cd.get('connection_id')

            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            # set wallet password
            # TODO vcx_config['something'] = raw_password

            connections = AgentConnection.objects.filter(id=connection_id, wallet__wallet_name=wallet_name).all()
            # TODO validate connection id
            my_connection = connections[0]

            # validate connection and get the updated status
            try:
                my_connection = check_connection_status(wallet, my_connection)

                return render(request, 'indy/form_response.html', {'msg': 'Updated connection for ' + wallet_name + ', ' + my_connection.partner_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to update request for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to update request for ' + wallet_name})

    else:
        # find connection request
        wallet_name = request.session['wallet_name']
        connection_id = request.GET.get('id', None)
        connections = AgentConnection.objects.filter(id=connection_id, wallet__wallet_name=wallet_name).all()

        form = PollConnectionStatusForm(initial={ 'connection_id': connection_id,
                                                  'wallet_name': connections[0].wallet.wallet_name })

    return render(request, 'indy/connection/status.html', {'form': form})


######################################################################
# views to offer, request, send and receive credentials
######################################################################
def check_connection_messages(request):
    if request.method=='POST':
        form = PollConnectionStatusForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            #now in the object cd, you have the form as a dictionary.
            connection_id = cd.get('connection_id')

            if connection_id > 0:
                connections = VcxConnection.objects.filter(wallet_name=wallet_name, id=connection_id).all()
            else:
                connections = VcxConnection.objects.filter(wallet_name=wallet_name).all()

            total_count = 0
            for connection in connections:
                # check for outstanding, un-received messages - add to outstanding conversations
                if connection.connection_type == 'Inbound':
                    wallet = connection.wallet_name
                    msg_count = handle_inbound_messages(wallet, json.loads(wallet.vcx_config), connection)
                    total_count = total_count + msg_count

            handle_wallet_login_internal(request, wallet_name, raw_password)

            return render(request, 'indy/form_response.html', {'msg': 'Received message count = ' + str(total_count)})

    else:
        # find connection request
        connection_id = request.GET.get('connection_id', None)
        if 'wallet_name' in request.session:
            wallet_name = request.session['wallet_name']
            if connection_id:
                connections = VcxConnection.objects.filter(wallet_name=wallet_name, id=connection_id).all()
            else:
                connection_id = 0
                connections = VcxConnection.objects.filter(wallet_name=wallet_name).all()
        # TODO validate connection id
        form = PollConnectionStatusForm(initial={ 'connection_id': connection_id,
                                                  'wallet_name': connections[0].wallet_name })

    return render(request, 'indy/check_messages.html', {'form': form})


def list_conversations(request):
    # expects a wallet to be opened in the current session
    if 'wallet_name' in request.session:
        wallet_name = request.session['wallet_name']
        conversations = VcxConversation.objects.filter(wallet_name=wallet_name).all()
        return render(request, 'indy/list_conversations.html', {'wallet_name': wallet_name, 'conversations': conversations})

    return render(request, 'indy/list_conversations.html', {'wallet_name': 'No wallet selected', 'conversations': []})


def handle_select_credential_offer(request):
    if request.method=='POST':
        form = SelectCredentialOfferForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)

            cd = form.cleaned_data

            connection_id = cd.get('connection_id')
            cred_def = cd.get('cred_def')

            connections = VcxConnection.objects.filter(id=connection_id).all()
            # TODO validate connection id
            schema_attrs = cred_def.creddef_template
            form = SendCredentialOfferForm(initial={ 'connection_id': connection_id,
                                                     'wallet_name': connections[0].wallet_name,
                                                     'cred_def': cred_def.id,
                                                     'schema_attrs': schema_attrs })

            handle_wallet_login_internal(request, wallet_name, raw_password)

            return render(request, 'indy/credential_offer.html', {'form': form})

    else:
        # find conversation request
        connection_id = request.GET.get('connection_id', None)
        connections = VcxConnection.objects.filter(id=connection_id).all()
        # TODO validate connection id
        form = SelectCredentialOfferForm(initial={ 'connection_id': connection_id,
                                                   'wallet_name': connections[0].wallet_name})

    return render(request, 'indy/select_credential_offer.html', {'form': form})


def handle_credential_offer(request):
    if request.method=='POST':
        form = SendCredentialOfferForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            #now in the object cd, you have the form as a dictionary.
            connection_id = cd.get('connection_id')
            credential_tag = cd.get('credential_tag')
            cred_def_id = cd.get('cred_def')
            schema_attrs = cd.get('schema_attrs')
            credential_name = cd.get('credential_name')

            # get user or org associated with this wallet
            related_user = User.objects.filter(wallet_name=wallet_name).all()
            related_org = AtriaOrganization.objects.filter(wallet_name=wallet_name).all()
            if len(related_user) == 0 and len(related_org) == 0:
                raise Exception('Error wallet with no owner {}'.format(wallet_name))
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            if 0 < len(related_user):
                vcx_config = wallet.vcx_config
                my_name = related_user[0].email
            elif 0 < len(related_org):
                vcx_config = wallet.vcx_config
                my_name = related_org[0].org_name

            connections = VcxConnection.objects.filter(id=connection_id).all()
            # TODO validate connection id
            my_connection = connections[0]
            connection_data = my_connection.connection_data

            cred_defs = IndyCredentialDefinition.objects.filter(id=cred_def_id).all()
            cred_def = cred_defs[0]

            # set wallet password
            # TODO vcx_config['something'] = raw_password

            # build the credential offer and send
            try:
                credential_data = send_credential_offer(wallet, json.loads(vcx_config), json.loads(connection_data), my_connection.partner_name, credential_tag, schema_attrs, cred_def, credential_name)

                my_conversation = VcxConversation(
                    wallet_name = wallet,
                    connection_partner_name = my_connection.partner_name,
                    conversation_type = 'CredentialOffer',
                    message_id = 'N/A',
                    status = 'Sent',
                    conversation_data = json.dumps(credential_data))
                my_conversation.save()

                print(" >>> Updated conversation for", wallet_name, )

                handle_wallet_login_internal(request, wallet_name, raw_password)

                return render(request, 'indy/form_response.html', {'msg': 'Updated conversation for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to update conversation for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to update conversation for ' + wallet_name})

    else:
        return render(request, 'indy/form_response.html', {'msg': 'Method not allowed'})


def handle_cred_offer_response(request):
    if request.method=='POST':
        form = SendCredentialResponseForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            conversation_id = cd.get('conversation_id')

            # get user or org associated with this wallet
            related_user = User.objects.filter(wallet_name=wallet_name).all()
            related_org = AtriaOrganization.objects.filter(wallet_name=wallet_name).all()
            if len(related_user) == 0 and len(related_org) == 0:
                raise Exception('Error wallet with no owner {}'.format(wallet_name))
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            if 0 < len(related_user):
                vcx_config = wallet.vcx_config
                my_name = related_user[0].email
            elif 0 < len(related_org):
                vcx_config = wallet.vcx_config
                my_name = related_org[0].org_name

            # find conversation request
            conversations = VcxConversation.objects.filter(id=conversation_id).all()
            # TODO validate conversation id
            my_conversation = conversations[0]
            indy_conversation = json.loads(my_conversation.conversation_data)
            connections = VcxConnection.objects.filter(wallet_name=my_conversation.wallet_name, partner_name=my_conversation.connection_partner_name).all()
            # TODO validate connection id
            my_connection = connections[0]

            # build the credential request and send
            try:
                credential_data = send_credential_request(wallet, json.loads(vcx_config), json.loads(my_connection.connection_data), my_connection.partner_name, my_conversation)

                my_conversation.status = 'Sent'
                my_conversation.conversation_data = json.dumps(credential_data)
                my_conversation.conversation_type = 'CredentialRequest'
                my_conversation.save()

                print(" >>> Updated conversation for", wallet_name, )

                handle_wallet_login_internal(request, wallet_name, raw_password)

                return render(request, 'indy/form_response.html', {'msg': 'Updated conversation for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to update conversation for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to update conversation for ' + wallet_name})

    else:
        # find conversation request, fill in form details
        conversation_id = request.GET.get('conversation_id', None)
        conversations = VcxConversation.objects.filter(id=conversation_id).all()
        # TODO validate conversation id
        conversation = conversations[0]
        indy_conversation = json.loads(conversation.conversation_data)
        connections = VcxConnection.objects.filter(wallet_name=conversation.wallet_name, partner_name=conversation.connection_partner_name).all()
        # TODO validate connection id
        connection = connections[0]
        form = SendCredentialResponseForm(initial={ 
                                                 'conversation_id': conversation_id,
                                                 'wallet_name': connection.wallet_name,
                                                 'from_partner_name': connection.partner_name,
                                                 'claim_id':indy_conversation['claim_id'],
                                                 'claim_name': indy_conversation['claim_name'],
                                                 'credential_attrs': indy_conversation['credential_attrs'],
                                                 'libindy_offer_schema_id': json.loads(indy_conversation['libindy_offer'])['schema_id']
                                                })

    return render(request, 'indy/cred_offer_response.html', {'form': form})


######################################################################
# views to request, send and receive proofs
######################################################################
def handle_proof_req_response(request):
    if request.method=='POST':
        form = SendProofReqResponseForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            conversation_id = cd.get('conversation_id')
            proof_req_name = cd.get('proof_req_name')

            # get user or org associated with this wallet
            related_user = User.objects.filter(wallet_name=wallet_name).all()
            related_org = AtriaOrganization.objects.filter(wallet_name=wallet_name).all()
            if len(related_user) == 0 and len(related_org) == 0:
                raise Exception('Error wallet with no owner {}'.format(wallet_name))
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            if 0 < len(related_user):
                vcx_config = wallet.vcx_config
                my_name = related_user[0].email
            elif 0 < len(related_org):
                vcx_config = wallet.vcx_config
                my_name = related_org[0].org_name

            # find conversation request
            conversations = VcxConversation.objects.filter(id=conversation_id).all()
            # TODO validate conversation id
            my_conversation = conversations[0]
            indy_conversation = json.loads(my_conversation.conversation_data)
            connections = VcxConnection.objects.filter(wallet_name=my_conversation.wallet_name, partner_name=my_conversation.connection_partner_name).all()
            # TODO validate connection id
            my_connection = connections[0]

            # find claims for this proof request and display for the user
            try:
                claim_data = get_claims_for_proof_request(wallet, json.loads(vcx_config), json.loads(my_connection.connection_data), my_connection.partner_name, my_conversation)

                form = SelectProofReqClaimsForm(initial={
                         'conversation_id': conversation_id,
                         'wallet_name': my_connection.wallet_name,
                         'from_partner_name': my_connection.partner_name,
                         'proof_req_name': proof_req_name,
                         'requested_attrs': json.dumps(claim_data),
                    })

                handle_wallet_login_internal(request, wallet_name, raw_password)

                return render(request, 'indy/proof_select_claims.html', {'form': form})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to find claims for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to find claims for ' + wallet_name})

    else:
        # find conversation request, fill in form details
        conversation_id = request.GET.get('conversation_id', None)
        conversations = VcxConversation.objects.filter(id=conversation_id).all()
        # TODO validate conversation id
        conversation = conversations[0]
        indy_conversation = json.loads(conversation.conversation_data)
        connections = VcxConnection.objects.filter(wallet_name=conversation.wallet_name, partner_name=conversation.connection_partner_name).all()
        # TODO validate connection id
        connection = connections[0]
        form = SendProofReqResponseForm(initial={ 
                                                 'conversation_id': conversation_id,
                                                 'wallet_name': connection.wallet_name,
                                                 'from_partner_name': connection.partner_name,
                                                 'proof_req_name': indy_conversation['proof_request_data']['name'],
                                                 'requested_attrs': indy_conversation['proof_request_data']['requested_attributes'],
                                                })

    return render(request, 'indy/proof_req_response.html', {'form': form})


def handle_proof_select_claims(request):
    if request.method=='POST':
        form = SelectProofReqClaimsForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            conversation_id = cd.get('conversation_id')
            proof_req_name = cd.get('proof_req_name')

            # get user or org associated with this wallet
            related_user = User.objects.filter(wallet_name=wallet_name).all()
            related_org = AtriaOrganization.objects.filter(wallet_name=wallet_name).all()
            if len(related_user) == 0 and len(related_org) == 0:
                raise Exception('Error wallet with no owner {}'.format(wallet_name))
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            if 0 < len(related_user):
                vcx_config = wallet.vcx_config
                my_name = related_user[0].email
            elif 0 < len(related_org):
                vcx_config = wallet.vcx_config
                my_name = related_org[0].org_name

            print("Look up conversation")
            # find conversation request
            conversations = VcxConversation.objects.filter(id=conversation_id).all()
            # TODO validate conversation id
            my_conversation = conversations[0]
            indy_conversation = json.loads(my_conversation.conversation_data)
            connections = VcxConnection.objects.filter(wallet_name=my_conversation.wallet_name, partner_name=my_conversation.connection_partner_name).all()
            # TODO validate connection id
            my_connection = connections[0]

            # get selected attributes for proof request
            print("Map requested attributes")
            requested_attributes = indy_conversation['proof_request_data']['requested_attributes']
            requested_predicates = indy_conversation['proof_request_data']['requested_predicates']
            credential_attrs = {}
            for attr in requested_attributes:
                field_name = 'proof_req_attr_' + attr
                credential_attrs[attr] = request.POST.get(field_name)
            for attr in requested_predicates:
                field_name = 'proof_req_attr_' + attr
                credential_attrs[attr] = request.POST.get(field_name)

            # send claims for this proof request to requestor
            try:
                proof_data = send_claims_for_proof_request(wallet, json.loads(vcx_config), json.loads(my_connection.connection_data), my_connection.partner_name, my_conversation, credential_attrs)

                my_conversation.status = 'Accepted'
                my_conversation.conversation_type = 'ProofOffer'
                my_conversation.conversation_data = json.dumps(proof_data)
                my_conversation.save()

                print(" >>> Updated conversation for", wallet_name, )

                handle_wallet_login_internal(request, wallet_name, raw_password)

                return render(request, 'indy/form_response.html', {'msg': 'Sent proof request for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to find claims for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to find claims for ' + wallet_name})

    else:
        return render(request, 'indy/form_response.html', {'msg': 'Method not allowed'})


def poll_conversation_status(request):
    if request.method=='POST':
        form = SendConversationResponseForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            conversation_id = cd.get('conversation_id')

            # get user or org associated with this wallet
            related_user = User.objects.filter(wallet_name=wallet_name).all()
            related_org = AtriaOrganization.objects.filter(wallet_name=wallet_name).all()
            if len(related_user) == 0 and len(related_org) == 0:
                raise Exception('Error wallet with no owner {}'.format(wallet_name))
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            if 0 < len(related_user):
                vcx_config = wallet.vcx_config
                my_name = related_user[0].email
            elif 0 < len(related_org):
                vcx_config = wallet.vcx_config
                my_name = related_org[0].org_name

            # find conversation request
            conversations = VcxConversation.objects.filter(id=conversation_id).all()
            # TODO validate conversation id
            my_conversation = conversations[0]
            indy_conversation = json.loads(my_conversation.conversation_data)
            connections = VcxConnection.objects.filter(wallet_name=my_conversation.wallet_name, partner_name=my_conversation.connection_partner_name).all()
            # TODO validate connection id
            my_connection = connections[0]

            # check conversation status
            try:
                polled_count = poll_message_conversation(wallet, json.loads(vcx_config), my_connection, my_conversation)

                print(" >>> Updated conversation for", wallet_name, )

                handle_wallet_login_internal(request, wallet_name, raw_password)

                return render(request, 'indy/form_response.html', {'msg': 'Updated conversation for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to update conversation for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to update conversation for ' + wallet_name})

    else:
        # find conversation request, fill in form details
        conversation_id = request.GET.get('conversation_id', None)
        conversations = VcxConversation.objects.filter(id=conversation_id).all()
        # TODO validate conversation id
        conversation = conversations[0]
        indy_conversation = json.loads(conversation.conversation_data)
        connections = VcxConnection.objects.filter(wallet_name=conversation.wallet_name, partner_name=conversation.connection_partner_name).all()
        # TODO validate connection id
        connection = connections[0]
        form = SendConversationResponseForm(initial={'conversation_id': conversation_id, 'wallet_name': connection.wallet_name})

    return render(request, 'indy/check_conversation.html', {'form': form})


def handle_select_proof_request(request):
    if request.method=='POST':
        form = SelectProofRequestForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            cd = form.cleaned_data

            #now in the object cd, you have the form as a dictionary.
            proof_request = cd.get('proof_request')
            connection_id = cd.get('connection_id')

            connections = VcxConnection.objects.filter(id=connection_id).all()
            connection = connections[0]
            connection_data = json.loads(connection.connection_data)
            institution_did = connection_data['data']['public_did']

            proof_req_attrs = proof_request.proof_req_attrs
            proof_req_predicates = proof_request.proof_req_predicates

            # selective attribute substitutions
            proof_req_attrs = proof_req_attrs.replace('$ISSUER_DID', institution_did)
            proof_req_predicates = proof_req_predicates.replace('$ISSUER_DID', institution_did)

            proof_form = SendProofRequestForm(initial={
                    'wallet_name': connection.wallet_name,
                    'connection_id': connection_id,
                    'proof_name': proof_request.proof_req_name,
                    'proof_attrs': proof_req_attrs,
                    'proof_predicates': proof_req_predicates})

            return render(request, 'indy/send_proof_request.html', {'form': proof_form})

    else:
        # find conversation request
        connection_id = request.GET.get('connection_id', None)
        connections = VcxConnection.objects.filter(id=connection_id).all()
        connection = connections[0]
        connection_data = json.loads(connection.connection_data)
        form = SelectProofRequestForm(initial={ 'connection_id': connection_id,
                                                'wallet_name': connection.wallet_name })

    return render(request, 'indy/select_proof_request.html', {'form': form})


def handle_send_proof_request(request):
    if request.method=='POST':
        form = SendProofRequestForm(request.POST)
        if not form.is_valid():
            return render(request, 'indy/form_response.html', {'msg': 'Form error', 'msg_txt': str(form.errors)})
        else:
            # log out of current wallet, if any
            wallet_name = request.session['wallet_name']
            raw_password = request.session['wallet_password']
            indy_wallet_logout(None, request.user, request)
    
            cd = form.cleaned_data

            #now in the object cd, you have the form as a dictionary.
            connection_id = cd.get('connection_id')
            proof_uuid = cd.get('proof_uuid')
            proof_name = cd.get('proof_name')
            proof_attrs = cd.get('proof_attrs')
            proof_predicates = cd.get('proof_predicates')

            # get user or org associated with this wallet
            related_user = User.objects.filter(wallet_name=wallet_name).all()
            related_org = AtriaOrganization.objects.filter(wallet_name=wallet_name).all()
            if len(related_user) == 0 and len(related_org) == 0:
                raise Exception('Error wallet with no owner {}'.format(wallet_name))
            wallet = IndyWallet.objects.filter(wallet_name=wallet_name).first()

            if 0 < len(related_user):
                vcx_config = wallet.vcx_config
                my_name = related_user[0].email
            elif 0 < len(related_org):
                vcx_config = wallet.vcx_config
                my_name = related_org[0].org_name

            connections = VcxConnection.objects.filter(id=connection_id).all()
            # TODO validate connection id
            my_connection = connections[0]
            connection_data = my_connection.connection_data

            # set wallet password
            # TODO vcx_config['something'] = raw_password

            # build the proof request and send
            try:
                conversation_data = send_proof_request(wallet, json.loads(vcx_config), json.loads(connection_data), my_connection.partner_name, proof_uuid, proof_name, proof_attrs, proof_predicates)

                my_conversation = VcxConversation(
                    wallet_name = wallet,
                    connection_partner_name = my_connection.partner_name,
                    conversation_type = 'ProofRequest',
                    message_id = 'N/A',
                    status = 'Sent',
                    conversation_data = json.dumps(conversation_data))
                my_conversation.save()

                print(" >>> Updated conversation for", wallet_name, )

                handle_wallet_login_internal(request, wallet_name, raw_password)

                return render(request, 'indy/form_response.html', {'msg': 'Updated conversation for ' + wallet_name})
            except IndyError:
                # ignore errors for now
                print(" >>> Failed to update conversation for", wallet_name)
                return render(request, 'indy/form_response.html', {'msg': 'Failed to update conversation for ' + wallet_name})

    else:
        return render(request, 'indy/form_response.html', {'msg': 'Method not allowed'})


def handle_view_proof(request):
    conversation_id = request.GET.get('conversation_id', None)
    conversations = VcxConversation.objects.filter(id=conversation_id).all()
    # TODO validate conversation id
    conversation = conversations[0]
    return render(request, 'indy/form_response.html', {'msg': "Proof Reveived", 'msg_txt': conversation.conversation_data})


######################################################################
# views to list wallet credentials
######################################################################
def form_response(request):
    msg = request.GET.get('msg', None)
    msg_txt = request.GET.get('msg_txt', None)
    return render(request, 'indy/form_response.html', {'msg': msg, 'msg_txt': msg_txt})


def list_wallet_credentials(request):
    if 'wallet_name' in request.session:
        wallet_name = request.session['wallet_name']
        wallet_handle = request.session['wallet_handle']

        (search_handle, search_count) = run_coroutine_with_args(prover_search_credentials, wallet_handle, "{}")
        credentials = run_coroutine_with_args(prover_fetch_credentials, search_handle, search_count)
        run_coroutine_with_args(prover_close_credentials_search, search_handle)

        return render(request, 'indy/list_credentials.html', {'wallet_name': wallet_name, 'credentials': json.loads(credentials)})

    return render(request, 'indy/list_credentials.html', {'wallet_name': 'No wallet selected', 'credentials': []})


