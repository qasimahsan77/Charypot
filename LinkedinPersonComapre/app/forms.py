"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
#from models import Profile
from app.models import Profile,TwitterProfile
#from django.db import models
#from django import models

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields={"name","occupation","workhistory","profileurl","headline","location","industry","summary","description","schoolname","companyname","imageurl","skills"}

class TwitterForm(forms.ModelForm):
    class Meta:
        model=TwitterProfile
        fields={"twitter_profile","twitter_username","profile_id","profile_location","imageurl","latest_post_link"}