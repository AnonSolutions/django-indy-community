from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login
from django.urls import reverse

from .forms import *
from .models import *
from .wallet_utils import *
from .registration_utils import *
from .agent_utils import *
from .signals import handle_wallet_login_internal


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
            org_role = ''
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

def individual_connections_view(request):
    return render(request, 'indy/individual_connections.html')

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

def organization_connections_view(request):
    return render(request, 'indy/organization_connections.html')

def organization_conversations_view(request):
    return render(request, 'indy/organization_conversations.html')

def organization_credentials_view(request):
    return render(request, 'indy/organization_credentials.html')


######################################################################
# views to create and confirm agent-to-agent connections
######################################################################


######################################################################
# views to offer, request, send and receive credentials
######################################################################


######################################################################
# views to request, send and receive proofs
######################################################################


######################################################################
# views to list wallet credentials
######################################################################


