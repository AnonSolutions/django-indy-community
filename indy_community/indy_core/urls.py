from django.urls import path, include
from django.conf.urls import url
from django.contrib.auth import views as auth_views

#from .forms import *
from .views import *


#app_name = "indy"

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', user_signup_view, name='signup'),
    path('org_signup/', org_signup_view, name='org_signup'),
    path('', auth_views.LoginView.as_view(), name='login'),
]


# URL patterns for all
sharedpatterns = [
    path('send_invitation/', handle_connection_request, name='send_invitation'),
    path('list_connections/', list_connections, name='list_connections'),
    path('connection_response/', handle_connection_response, name='connection_response'),
    path('check_connection/', poll_connection_status, name='check_connection'),
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
]

# URL patterns specific to individuals
individualpatterns = [
    path('', include([
        path('profile/', individual_profile_view, name='profile'),
        path('wallet/', individual_wallet_view, name='wallet'),
        path('connections/', list_connections, name='connections'),
        path('conversations/', list_conversations, name='conversations'),
        path('credentials/', list_wallet_credentials, name='credentials'),
        ])),
    path('', include(sharedpatterns)),
]

# URL patterns accessible only to organizations
organizationpatterns = [
    path('', include([
        path('profile/', organization_profile_view, name='profile'),
        path('data/', organization_data_view, name='org_data'),
        path('wallet/', organization_wallet_view, name='wallet'),
        path('connections/', list_connections, name='connections'),
        path('conversations/', list_conversations, name='conversations'),
        path('credentials/', list_wallet_credentials, name='credentials'),
        ])),
    path('', include(sharedpatterns)),
]

urlpatterns.append(path('individual/', include((individualpatterns, 'indy'), namespace='individual')))
urlpatterns.append(path('organization/', include((organizationpatterns, 'indy'), namespace='organization')))


