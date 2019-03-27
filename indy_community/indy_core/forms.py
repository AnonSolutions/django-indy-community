from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import *


class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=150, required=False,
                                help_text='Optional.')
    email = forms.EmailField(
        max_length=254, help_text='Required. Provide a valid email address.')

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


class OrganizationSignUpForm(UserSignUpForm):
    org_name = forms.CharField(max_length=40, required=True,
                                 help_text='Required.')
    org_role_name = forms.CharField(max_length=40, required=True,
                                 help_text='Required.')
