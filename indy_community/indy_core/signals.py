from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model

import json

from .models import *
from .tasks import *
from .wallet_utils import *


def url_namespace(role):
    if role == 'Admin':
        return 'organization:'
    else:
        return 'individual:'


def user_wallet_logged_in_handler(request, user, wallet_name):
    print("Login wallet, {} {} {}".format(user.email, request.session.session_key, wallet_name))
    (session, session_created) = IndySession.objects.get_or_create(user=user, session_id=request.session.session_key)
    session.wallet_name = wallet_name
    session.save()

def user_wallet_logged_out_handler(request, user):
    print("Logout wallet, {} {}".format(user.email, request.session.session_key))
    session = IndySession.objects.get(user=user, session_id=request.session.session_key)
    session.wallet_name = None
    session.save()

def user_logged_in_handler(sender, request, user, **kwargs):
    if 'wallet_name' in request.session:
        wallet_name = request.session['wallet_name']
    else:
        wallet_name = None
    print("Login user {} {} {}".format(user.email, request.session.session_key, wallet_name))
    (session, session_created) = IndySession.objects.get_or_create(user=user, session_id=request.session.session_key, wallet_name=wallet_name)
    agent_background_task("Started by user login", user.id, request.session.session_key, repeat=20)


def user_logged_out_handler(sender, user, request, **kwargs):
    print("Logout user {} {}".format(user.email, request.session.session_key))
    indy_wallet_logout(sender, user, request, **kwargs)
    IndySession.objects.get(user=user, session_id=request.session.session_key).delete()


def handle_wallet_login_internal(request, wallet_name, raw_password):
    # get user or org associated with this wallet
    related_user = get_user_model().objects.filter(wallet__wallet_name=wallet_name).all()
    related_org = IndyOrganization.objects.filter(wallet__wallet_name=wallet_name).all()
    if len(related_user) == 0 and len(related_org) == 0:
        raise Exception('Error wallet with no owner {}'.format(wallet_name))

    # now try to open the wallet - will throw an exception if it fails
    wallet_handle = open_wallet(wallet_name, raw_password)
    close_wallet(wallet_handle)

    if len(related_user) > 0:
        request.session['wallet_type'] = 'user'
        request.session['wallet_owner'] = related_user[0].email
    elif len(related_org) > 0:
        request.session['wallet_type'] = 'org'
        request.session['wallet_owner'] = related_org[0].org_name
    request.session['wallet_name'] = wallet_name
    request.session['wallet_password'] = raw_password

    user_wallet_logged_in_handler(request, request.user, wallet_name)


def handle_wallet_logout_internal(request):
    # clear wallet-related session variables
    if 'wallet_type' in request.session:
        del request.session['wallet_type']
    if 'wallet_name' in request.session:
        del request.session['wallet_name']
    if 'wallet_password' in request.session:
        del request.session['wallet_password']
    if 'wallet_owner' in request.session:
        del request.session['wallet_owner']


def init_user_session(sender, user, request, **kwargs):
    target = request.POST.get('next', '/individual/')
    if 'organization' in target and user.has_role('Admin'):
        request.session['ACTIVE_ROLE'] = 'Admin'
        orgs = IndyOrgRelationship.objects.filter(user=user).all()
        if 0 < len(orgs):
            sel_org = orgs[0].org
            request.session['ACTIVE_ORG'] = str(sel_org.id)

            # login as org wallet
            if sel_org.wallet is not None:
                sel_wallet = sel_org.wallet
                config = json.loads(sel_wallet.wallet_config)
                handle_wallet_login_internal(request, config['wallet_name'], config['wallet_key'])
    else:
        if user.has_role('User'):
            request.session['ACTIVE_ROLE'] = 'User'
        else:
            # TODO for now just set a dummy default - logged in user with no role assigned
            request.session['ACTIVE_ROLE'] = 'User'

        # try to login as user wallet
        if user.wallet is not None:
            sel_wallet = user.wallet
            config = json.loads(sel_wallet.wallet_config)
            handle_wallet_login_internal(request, config['wallet_name'], config['wallet_key'])

    role = request.session['ACTIVE_ROLE']
    namespace = url_namespace(role)
    request.session['URL_NAMESPACE'] = namespace


def clear_user_session(sender, user, request, **kwargs):
    handle_wallet_logout_internal(request)

    if 'ACTIVE_ROLE' in request.session:
        del request.session['ACTIVE_ROLE']
    if 'ACTIVE_ORG' in request.session:
        del request.session['ACTIVE_ORG']
    request.session['URL_NAMESPACE'] = ''


user_logged_in.connect(init_user_session)

user_logged_out.connect(clear_user_session)


