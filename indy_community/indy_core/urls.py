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

# URL patterns specific to individuals
individualpatterns = [
    path('', include([
        path('profile/', individual_profile_view, name='profile'),
        path('wallet/', individual_wallet_view, name='wallet'),
        path('connections/', individual_connections_view, name='connections'),
        path('conversations/', individual_conversations_view, name='conversations'),
        path('credentials/', individual_credentials_view, name='credentials'),
        ])),
]

# URL patterns accessible only to organizations
organizationpatterns = [
    path('', include([
        path('profile/', organization_profile_view, name='profile'),
        path('data/', organization_data_view, name='org_data'),
        path('wallet/', organization_wallet_view, name='wallet'),
        path('connections/', organization_connections_view, name='connections'),
        path('conversations/', organization_conversations_view, name='conversations'),
        path('credentials/', organization_credentials_view, name='credentials'),
        ])),
]

urlpatterns.append(path('individual/', include((individualpatterns, 'indy'), namespace='individual')))
urlpatterns.append(path('organization/', include((organizationpatterns, 'indy'), namespace='organization')))


