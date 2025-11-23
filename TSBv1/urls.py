
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static 
from django.contrib.auth import views as auth_view
from .forms import LoginForm, MyPasswordResetForm, MyPasswordChangeForm, MyPasswordResetForm,MySetPasswordForm
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout


urlpatterns = [
    path("", views.home, name="home"),
    path("index2/", views.index2, name="index2"),
    path("services/", views.services_page, name="services"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("termsandconditions/", views.termsandconditions, name="termsandconditions"),
    path("privacypolicy/", views.privacypolicy, name="privacypolicy"),
    path("refundpolicy/", views.refundpolicy, name="refundpolicy"),
    path("shippingpolicy/", views.shippingpolicy, name="shippingpolicy"),


    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("payments/", views.payments, name="payments"),
    path("add-to-cart/",views.add_to_cart, name="add-to-cart"),

    path("cart/",views.show_cart, name="showcart"),
    path('paymentdone/', views.payment_done, name='paymentdone'),

    path("checkout/",views.checkout.as_view(), name="checkout"),

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
    path("accounts/login/", auth_view.LoginView.as_view(template_name='app/customerlogin.html', authentication_form=LoginForm), name="customerlogin"),
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
        

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
