from django.db.models import Count
from .models import Services, Customer, Cart
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import CustomerRegistrationForm,MyPasswordResetForm, CustomerProfileForm
from django.contrib.auth import logout
from django.conf import settings
from django.shortcuts import redirect
from django.db.models import Q
from django.http import HttpResponse
import razorpay


key_id = getattr(settings, 'razor_pay_key_id', None)
if key_id:
    print(key_id)

# Create your views here.

def home(request):
    return render(request,"app/index.html")

def index2(request):
    return render(request,"app/index2.html")

def about(request):
    return render(request,"app/about.html")

def contact(request):
    return render(request,"app/contact.html")

def termsandconditions(request):
    return render(request,"app/termsandcontions.html")
def privacypolicy(request):
    return render(request,"app/privacypolicy.html")
def refundpolicy(request):
    return render(request,"app/refundpolicy.html")
def shippingpolicy(request):
    return render(request,"app/shippingpolicy.html")



#Category Page Logic main branch use case
class CategoryViewNoSlug(View):
    def get(self, request):
        return render(request, "app/category.html",locals())

class CategoryView(View):
    def get(self, request, val):
        services = Services.objects.filter(category=val).prefetch_related('images')
        title = Services.objects.filter(category=val).values('title')
        return render(request, "app/category.html",locals())
    
class CategoryTitle(View):
    def get(self, request, val):
        services = Services.objects.filter(title=val).prefetch_related('images')
        title = Services.objects.filter(category=services[0].category).values('title')
        return render(request, "app/category.html",locals())
    
class CategoryDetail(View):
    def get(self, request,pk):
        services = Services.objects.prefetch_related('images').get(pk=pk)
        return render(request, "app/categorydetail.html",locals())
    
#Customer Registration Logic
class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, "app/customerregistration.html",locals())
    
    #User POST registration form method
    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Congratulations! You have successfully registered.")
            form = CustomerRegistrationForm()
        else:
            messages.error(request, "Registration failed. Please try again.")

        return render(request, "app/customerregistration.html",locals())
    
#Customer Login Logic
class CustomerLoginview(View):
    def get(self, request):
        return render(request, "app/customerlogin.html",locals())
    
    def post(self, request):
        return render(request, "app/customerlogin.html",locals())
    
class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        return render(request, "app/profile.html",locals())
    def post(Self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']

            reg = Customer(user=user, name=name, locality=locality, city=city, mobile=mobile, state=state,zipcode=zipcode)
            reg.save()
            messages.success(request,"Congratulations! Profile Saved Successfully")
        else:
            messages.warning(request,"Invalid Input Data!")
        return render(request, "app/profile.html",locals())

def payments(request):
    return render(request, 'app/payments.html',locals())
    
def logout_user(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('customerlogin')

def add_to_cart(request):
    
    user = request.user
    services_id = request.GET.get('serv_id')
    services = Services.objects.get(id = services_id)
    Cart(user=user,services=services).save()
    return redirect("/cart")

def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user).select_related('services').prefetch_related('services__images')
    amount = 0
    for p in cart:
        value = p.quantity * p.services.discounted_price
        amount = amount + value
    totalamount= amount + 1
    razoramount= int(totalamount * 100)

    #client = razorpay.Client(auth = (settings.razor_pay_key_id, settings.key_secret))
    #payment = client.order.create({'amount': razoramount, 'currency': 'INR', 'payment_capture': '1'})

    print("###############")
    print('AAA')
    print("###############")

    data = {
        'amount': razoramount,
        'currency': 'INR',
        'receipt': 'order_rcptid_12'
        }
    return render(request, 'app/addtocart.html',locals())

def payment_done(request):
    order_id = request.GET.get('order_id')
    payment_id = request.GET.get('payment_id')
    cust_id = request.GET.get('cust_id')

    # You can add logic to update payment status, store in DB, etc.
    return render(request, 'paymentdone.html', {
        'order_id': order_id,
        'payment_id': payment_id,
        'cust_id': cust_id
    })

class checkout(View):
    def get(self, request):
        return render(request, 'app/checkout.html',locals())

def plus_cart(request):
    if request.method=='GET':

        serv_id = request.GET['serv_id']
        print(serv_id)
        c = Cart.objects.get(Q(services=serv_id) & Q(user=request.user))
        c.quantity += 1
        c.save()

        user = request.user
        cart = Cart.objects.filter(user=user)
        amount =0
        for p in cart:
            value = p.quantity * p.services.discounted_price
            amount = amount + value
        totalamount = amount + 40

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': totalamount
        }
        return JsonResponse(data)
    
def minus_cart(request):
    if request.method=='GET':
        serv_id = request.GET['serv_id']
        print(serv_id)
        c = Cart.objects.get(Q(services=serv_id) & Q(user=request.user))
        c.quantity -= 1
        c.save()

        user = request.user
        cart = Cart.objects.filter(user=user)
        amount =0
        for p in cart:
            value = p.quantity * p.services.discounted_price
            amount = amount + value
        totalamount = amount + 40

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': totalamount
        }
        return JsonResponse(data)
    
def remove_cart(request):
    if request.method=='GET':
        serv_id = request.GET['serv_id']
        c = Cart.objects.get(Q(services=serv_id) & Q(user=request.user))
        c.delete()

        user = request.user
        cart = Cart.objects.filter(user=user)
        amount =0
        for p in cart:
            value = p.quantity * p.services.discounted_price
            amount = amount + value
        totalamount = amount + 40

        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': totalamount
        }
        return JsonResponse(data)
