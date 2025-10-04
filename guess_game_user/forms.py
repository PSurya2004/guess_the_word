from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class PlayerRegistrationForm(UserCreationForm):
    # This form will automatically include the fields for
    # username and password from the UserCreationForm.
    # You can add more fields here if needed.
    # For example, to add the 'user_type', you would do:
    # user_type = forms.CharField(initial='player', widget=forms.HiddenInput())
    # but since you've set a default, it's not strictly necessary.

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('user_type',)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check for minimum 5 letters (both upper and lower case)
        if len(username) < 5 or not any(c.isalpha() for c in username) or not any(c.islower() for c in username) or not any(c.isupper() for c in username):
            raise forms.ValidationError("Username must be at least 5 characters and contain both upper and lower case letters.")
        return username

    def clean_password2(self):
        password = self.cleaned_data.get('password2')
        # Password validation: 5 characters, alpha, numeric, and special character
        if len(password) < 5 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password) or not any(c in '$,%*@' for c in password):
            raise forms.ValidationError("Password must be at least 5 characters and contain at least one alpha, one numeric, and one of '$', '%', '*', '@'.")
        return password
