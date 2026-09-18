from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, SchoolSettings, AccessRequest

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'first_name', 'last_name', 
                 'phone', 'date_of_birth', 'gender')

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'address',
            'profile_picture',
            'date_of_birth',
            'gender',
            'blood_group',
            'nationality',
        )


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Your current password was entered incorrectly.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two new password fields didn’t match.")

        # Optional: validate password strength
        password_validation.validate_password(password1, self.user)
        return cleaned_data

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = SchoolSettings
        fields = [
            'school_name',
            'school_address',
            'school_phone',
            'school_email',
            'school_logo',
            'current_session',
            'current_term',
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'school_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'school_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'school_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'current_session': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2023-2024'}),
            'current_term': forms.Select(attrs={'class': 'form-select'}),
        }


class AccessRequestForm(forms.ModelForm):
    """Form for users to request access to the school system"""
    
    class Meta:
        model = AccessRequest
        fields = ['email', 'user_type', 'first_name', 'last_name', 'phone', 'reason']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'required': True
            }),
            'user_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Doe',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 000-0000',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please explain why you need access to the school system...',
                'required': True
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email already has an account
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists. Please log in instead."
            )
        # Check if there's already a pending request
        if AccessRequest.objects.filter(email=email, status='pending').exists():
            raise forms.ValidationError(
                "You have already submitted an access request. Please wait for approval."
            )
        return email


class AdminAccessRequestForm(forms.ModelForm):
    """Form for admins to manage access requests"""
    
    class Meta:
        model = AccessRequest
        fields = ['status', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain why this request was rejected (optional)'
            }),
        }