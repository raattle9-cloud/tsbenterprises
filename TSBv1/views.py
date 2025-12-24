from django.db.models import Count
from .models import Services, Customer, Cart, Wishlist, CATEGORY_CHOICES
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

def health_check(request):
    """
    Health check endpoint for monitoring and keeping the app alive.
    Returns JSON response with status and timestamp.
    """
    from django.utils import timezone
    return JsonResponse({
        'status': 'healthy',
        'message': 'Backend is running',
        'timestamp': timezone.now().isoformat()
    })

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


def services_page(request):
    # Get all services with images
    services = Services.objects.all().prefetch_related('images')
    
    # Get wishlist items for authenticated users
    wishlist_service_ids = set()
    if request.user.is_authenticated:
        wishlist_service_ids = set(Wishlist.objects.filter(user=request.user).values_list('services_id', flat=True))
    
    # Prepare categories list for sidebar
    categories = []
    for code, label in CATEGORY_CHOICES:
        display_label = label.replace('_', ' ').title()
        categories.append({
            'code': code,
            'label': display_label
        })
    
    return render(request, "app/services.html", {
        "services": services,
        "categories": categories,
        "wishlist_service_ids": wishlist_service_ids,
        "CATEGORY_CHOICES": CATEGORY_CHOICES
    })



#Category Page Logic main branch use case
class CategoryViewNoSlug(View):
    def get(self, request):
        # Get all categories for sidebar
        categories = []
        for code, label in CATEGORY_CHOICES:
            display_label = label.replace('_', ' ').title()
            categories.append({
                'code': code,
                'label': display_label
            })
        return render(request, "app/category.html", locals())

class CategoryView(View):
    def get(self, request, val):
        services = Services.objects.filter(category=val).prefetch_related('images')
        # Get all categories for sidebar (not individual service titles)
        categories = []
        for code, label in CATEGORY_CHOICES:
            display_label = label.replace('_', ' ').title()
            categories.append({
                'code': code,
                'label': display_label
            })
        return render(request, "app/category.html", locals())
    
class CategoryTitle(View):
    def get(self, request, val):
        services = Services.objects.filter(title=val).prefetch_related('images')
        # Get all categories for sidebar (not individual service titles)
        categories = []
        for code, label in CATEGORY_CHOICES:
            display_label = label.replace('_', ' ').title()
            categories.append({
                'code': code,
                'label': display_label
            })
        return render(request, "app/category.html", locals())
    
class CategoryDetail(View):
    def get(self, request,pk):
        services = Services.objects.prefetch_related('images').get(pk=pk)
        # Check if item is in wishlist
        in_wishlist = False
        if request.user.is_authenticated:
            in_wishlist = Wishlist.objects.filter(user=request.user, services=services).exists()
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
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to add items to your cart.")
        return redirect('customerlogin')
    
    user = request.user
    services_id = request.GET.get('serv_id')
    services = Services.objects.get(id = services_id)
    # Use get_or_create to avoid creating duplicate Cart rows for the same user+service
    cart_item, created = Cart.objects.get_or_create(user=user, services=services, defaults={'quantity': 1})
    if not created:
        cart_item.quantity = (cart_item.quantity or 0) + 1
        cart_item.save()
    return redirect("/cart")

def show_cart(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to view your cart.")
        return redirect('customerlogin')
    
    user = request.user
    cart = Cart.objects.filter(user=user).select_related('services').prefetch_related('services__images')
    amount = 0
    for p in cart:
        value = p.quantity * p.services.discounted_price
        amount = amount + value
    totalamount= amount + 40
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
        # Accept either 'serv_id' (used in some templates) or 'prod_id' (used elsewhere)
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)
        print(serv_id)
        # Operate on the first matching cart item; get_or_create ensures duplicates are unlikely
        c = Cart.objects.filter(Q(services=serv_id) & Q(user=request.user)).first()
        if not c:
            # create a new one if missing
            services = Services.objects.get(id=serv_id)
            c = Cart.objects.create(user=request.user, services=services, quantity=1)
        else:
            c.quantity = (c.quantity or 0) + 1
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
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)
        print(serv_id)
        c = Cart.objects.filter(Q(services=serv_id) & Q(user=request.user)).first()
        if not c:
            return JsonResponse({'error': 'cart item not found'}, status=404)
        c.quantity = (c.quantity or 0) - 1
        if c.quantity <= 0:
            c.delete()
        else:
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
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)

        qs = Cart.objects.filter(Q(services=serv_id) & Q(user=request.user))
        if not qs.exists():
            return JsonResponse({'error': 'cart item not found'}, status=404)

        # Sum quantities across any duplicate rows to report removed quantity
        removed_quantity = sum((item.quantity or 0) for item in qs)
        # Delete all matching rows
        qs.delete()

        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.services.discounted_price
            amount = amount + value
        totalamount = amount + 40

        data = {
            'quantity': removed_quantity,
            'amount': amount,
            'totalamount': totalamount
        }
        return JsonResponse(data)

def plus_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        serv_id = request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing prod_id'}, status=400)
        
        try:
            user = request.user
            services = Services.objects.get(id=serv_id)
            
            # Check if item already exists in wishlist
            wishlist_item, created = Wishlist.objects.get_or_create(user=user, services=services)
            
            if created:
                message = 'Item added to wishlist'
            else:
                message = 'Item already in wishlist'
            
            return JsonResponse({'message': message, 'added': created})
        except Services.DoesNotExist:
            return JsonResponse({'error': 'Service not found'}, status=404)

def minus_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        serv_id = request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing prod_id'}, status=400)
        
        user = request.user
        # Use queryset.delete() instead of object.delete() to avoid MongoDB/Djongo id issue
        wishlist_qs = Wishlist.objects.filter(user=user, services__id=serv_id)
        deleted_count = wishlist_qs.count()
        
        if deleted_count > 0:
            wishlist_qs.delete()
            message = 'Item removed from wishlist'
        else:
            message = 'Item not found in wishlist'
        
        return JsonResponse({'message': message, 'removed': deleted_count > 0})

def show_wishlist(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to view your wishlist.")
        return redirect('customerlogin')
    
    user = request.user
    wishlist = Wishlist.objects.filter(user=user).select_related('services').prefetch_related('services__images')
    return render(request, 'app/wishlist.html', {'wishlist': wishlist})
