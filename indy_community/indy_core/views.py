from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login
from django.urls import reverse

from .forms import *
from .models import *
from .wallet_utils import *
from .registration_utils import *
from .agent_utils import *


# Sign up as a site user, and create a wallet
def user_signup_view(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            print(" >>> registered", username)

            # create an Indy wallet - derive wallet name from email, and re-use raw password
            wallet_name = get_user_wallet_name(username)
            print(" >>> create", wallet_name)
            wallet_handle = create_wallet(wallet_name, raw_password)

            # save the indy wallet first
            wallet = IndyWallet(wallet_name=wallet_name)
            wallet.save()

            user.wallet_name = wallet
            user.save()

            # provision VCX for this Org/Wallet
            config = initialize_and_provision_vcx(wallet_name, raw_password, username)
            wallet.wallet_config = config
            wallet.save()
            print(" >>> created wallet", wallet_name)

            # TODO need to auto-login with Atria custom user
            #login(request, user)

            return redirect('individual:profile')
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
            print(" >>> registered", username)

            # create an Indy wallet - derive wallet name from email, and re-use raw password
            wallet_name = get_user_wallet_name(username)
            print(" >>> create", wallet_name)
            wallet_handle = create_wallet(wallet_name, raw_password)

            # save the indy wallet first
            wallet = IndyWallet(wallet_name=wallet_name)
            wallet.save()

            user.wallet_name = wallet
            user.save()

            # provision VCX for this Org/Wallet
            config = initialize_and_provision_vcx(wallet_name, raw_password, username)
            wallet.wallet_config = config
            wallet.save()
            print(" >>> created wallet", wallet_name)

            # TODO need to auto-login with Atria custom user
            #login(request, user)

            return redirect('organization:profile')
    else:
        form = OrganizationSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def individual_profile_view(request):
    return render(request, 'indy/individual_profile.html')

def organization_profile_view(request):
    return render(request, 'indy/organization_profile.html')
