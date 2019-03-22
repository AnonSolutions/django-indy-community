from django.urls import path, include
from django.conf.urls import url
from django.contrib.auth import views as auth_views

#from .forms import *
from .views import *


#app_name = "indy"

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', signup_view, name='signup'),
    path('', auth_views.LoginView.as_view(), name='login'),
]

# URL patterns specific to individuals
individualpatterns = [
    path('', include([
        path('profile/', individual_profile_view, name='profile'),
        ])),
]

# URL patterns accessible only to organizations
organizationpatterns = [
    path('', include([
        path('profile/', organization_profile_view, name='profile'),
        ])),
]

urlpatterns.append(path('individual/', include((individualpatterns, 'indy'), namespace='individual')))
urlpatterns.append(path('organization/', include((organizationpatterns, 'indy'), namespace='organization')))


