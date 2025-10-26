from pyexpat.errors import messages
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .models import Customer


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs= {'class': 'form-control'}), label='Password')

    class Meta:
        model = User
        fields = ['username', 'password']


class CustomerRegistrationForm(UserCreationForm):
    username = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=15,widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=15,widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField( max_length=100, label='Email', required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Password confirmation')


    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Old password", widget=forms.PasswordInput(attrs={'class':'form-control'}))
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput(attrs={'class':'form-control'}))
    new_password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={'class':'form-control'}))

class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))

class MySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput(attrs={'class':'form-control'}))
    new_password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={'class':'form-control'}))



class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'mobile', 'locality', 'city', 'state', 'zipcode']
        widgets = {
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'mobile':forms.NumberInput(attrs={'class':'form-control'}),
            'locality':forms.TextInput(attrs={'class':'form-control'}),
            'city':forms.TextInput(attrs={'class':'form-control'}),
            'state':forms.Select(attrs={'class':'form-control'}),
            'zipcode':forms.NumberInput(attrs={'class':'form-control'}),

        }

def LogoutView(request):
    if request.method=="POST":
        messages.success(request, "You have successfully logged out.")
    return redirect('customerlogin')

