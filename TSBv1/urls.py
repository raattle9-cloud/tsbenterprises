

from django.urls import path
from . import views
from . import advance_booking_views
from . import auth_views as custom_auth_views
from django.contrib.auth import views as auth_view
from .forms import LoginForm, MyPasswordResetForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm



urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("", views.home, name="home"),
    path("index2/", views.index2, name="index2"),
    path("services/", views.services_page, name="services"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("termsandconditions/", views.termsandconditions, name="termsandconditions"),
    path("privacypolicy/", views.privacypolicy, name="privacypolicy"),
    path("refundpolicy/", views.refundpolicy, name="refundpolicy"),
    path("shippingpolicy/", views.shippingpolicy, name="shippingpolicy"),
    
    # Portal Hub - unified access to all portals
    path("hub/", views.portal_hub, name="portal-hub"),


    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("payments/", views.payments, name="payments"),
    path("add-to-cart/",views.add_to_cart, name="add-to-cart"),

    path("cart/",views.show_cart, name="showcart"),
    path('paymentdone/', views.payment_done, name='paymentdone'),

    path("checkout/",views.checkout.as_view(), name="checkout"),
    path("checkout/buynow/<int:service_id>/", views.checkout_buynow, name="checkout-buynow"),

    path('pluscart/', views.plus_cart, name="plus-cart"),
    path('minuscart/', views.minus_cart, name="minus-cart"),
    path('removecart/', views.remove_cart, name="remove-cart"),

    path('pluswishlist/', views.plus_wishlist, name="plus-wishlist"),
    path('minuswishlist/', views.minus_wishlist, name="minus-wishlist"),
    path('wishlist/', views.show_wishlist, name="showwishlist"),



    # No slug value empty category page url
    path("category/", views.CategoryViewNoSlug.as_view(), name="mainCategoryNoSlug"),
    
    # val is a variable that will be passed to the view.py in categoryView Class.
    path("category/<slug:val>/", views.CategoryView.as_view(), name="mainCategory"),
    path("category-title/<val>", views.CategoryTitle.as_view(), name="category-title"),
    path("category-detail/<int:pk>/", views.CategoryDetail.as_view(), name="category-detail"),



    #Customer Authentication url's
    path("registration/", views.CustomerRegistrationView.as_view(), name="customerregistration"),
    path("accounts/login/", custom_auth_views.StaffAwareLoginView.as_view(template_name='app/customerlogin.html', authentication_form=LoginForm), name="customerlogin"),
    path("password-reset/", auth_view.PasswordResetView.as_view(template_name='app/password_reset.html', form_class=MyPasswordResetForm), name="password_reset"),
   
    path("passwordchange/", auth_view.PasswordChangeView.as_view(template_name='app/changepassword.html', form_class=MyPasswordChangeForm, success_url='/passwordchangedone'), name="passwordchange"),
    
    path("passwordchangedone/", auth_view.PasswordChangeDoneView.as_view(template_name='app/passwordchangedone.html'), name="passwordchangedone"),
    path("logout/",views.logout_user, name="logout"),

    # Password reset url's####
    path('password-reset/',auth_view.PasswordResetView.as_view(template_name='app/password_reset.html',form_class=MyPasswordResetForm),name='password_reset'),
    path('password-reset/done/',auth_view.PasswordResetDoneView.as_view(template_name='app/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',auth_view.PasswordResetConfirmView.as_view(template_name='app/password_reset_confirm.html',form_class=MySetPasswordForm),name='password_reset_confirm'),
    path('password-reset-complete/',auth_view.PasswordResetCompleteView.as_view(template_name='app/password_reset_complete.html'),name='password_reset_complete'),
    ##################
    
    # Advance Booking URLs
    path('checkout/advance/<int:service_id>/', advance_booking_views.advance_booking_checkout, name='advance-checkout'),
    path('checkout/advance-payment/<int:booking_id>/', advance_booking_views.advance_payment_process, name='advance-payment'),
    path('booking/confirmation/<int:booking_id>/', advance_booking_views.advance_booking_confirmation, name='advance-booking-confirmation'),
    path('my-bookings/', advance_booking_views.my_advance_bookings, name='my-bookings'),
    
    # Staff Verification URLs
    path('staff/verify/', advance_booking_views.staff_verify, name='staff-verify'),
    
    # Staff API endpoints
    path('api/verify-booking/', advance_booking_views.verify_booking_api, name='verify-booking-api'),
    path('api/mark-verified/', advance_booking_views.mark_booking_verified, name='mark-verified-api'),

]
