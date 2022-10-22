from django import forms
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Add a valid email address.')

    class Meta:
        model = User
        fields = ("username", "email",)
