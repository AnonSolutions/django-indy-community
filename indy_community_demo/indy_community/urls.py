from django.urls import path, include
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf import settings

#from .forms import *
from .views import *


#app_name = "indy"

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', user_signup_view, name='signup'),
    path('org_signup/', org_signup_view, name='org_signup'),
    path('mobile_request/', mobile_request_connection, name='mobile_request'),
    path('send_invitation/', handle_connection_request, name='send_invitation'),
    path('list_connections/', list_connections, name='list_connections'),
    path('connection_response/', handle_connection_response, name='connection_response'),
    path('check_connection/', poll_connection_status, name='check_connection'),
    path('invitation/<token>', connection_qr_code, name='connection_qr'),
    path('form_response/', form_response, name='form_response'),
    path('check_messages/', check_connection_messages, name='check_messages'),
    path('list_conversations/', list_conversations, name='list_conversations'),
    path('cred_offer_response/', handle_cred_offer_response, name='cred_offer_response'),
    path('proof_req_response/', handle_proof_req_response, name='proof_req_response'),
    path('proof_select_claims/', handle_proof_select_claims, name='proof_select_claims'),
    path('select_credential_offer/', handle_select_credential_offer, name='select_credential_offer'),
    path('credential_offer/', handle_credential_offer, name='credential_offer'),
    path('select_proof_request/', handle_select_proof_request, name='select_proof_request'),
    path('send_proof_request/', handle_send_proof_request, name='send_proof_request'),
    path('view_proof/', handle_view_proof, name='view_proof'),
    path('check_conversation/', poll_conversation_status, name='check_conversation'),
    path('list_credentials/', list_wallet_credentials, name='list_credentials'),
    path('profile/', plugin_view, name='indy_profile', kwargs={'view_name': 'INDY_PROFILE_VIEW'}),
    path('data/', plugin_view, name='indy_data', kwargs={'view_name': 'INDY_DATA_VIEW'}),
    path('wallet/', plugin_view, name='indy_wallet', kwargs={'view_name': 'INDY_WALLET_VIEW'}),
    path('connections/', list_connections, name='connections'),
    path('conversations/', list_conversations, name='conversations'),
    path('credentials/', list_wallet_credentials, name='credentials'),
    path('', auth_views.LoginView.as_view(), name='login'),
]

