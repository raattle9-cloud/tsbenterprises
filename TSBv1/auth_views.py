"""
Custom login view that redirects staff users to the staff verification portal
"""
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse


class StaffAwareLoginView(auth_views.LoginView):
    """
    Custom login view that checks if user is a staff member and redirects accordingly
    """
    
    def form_valid(self, form):
        """Override to add staff redirect logic"""
        # Perform the standard login
        response = super().form_valid(form)
        
        # Check if user is in the Staff group
        user = self.request.user
        if user.groups.filter(name='Staff').exists():
            # Redirect staff users to the verification portal
            return redirect('staff-verify')
        
        # Regular users go to profile (default redirect from settings.LOGIN_REDIRECT_URL)
        return response
