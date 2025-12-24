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
        
        # Get wishlist items for authenticated users
        wishlist_service_ids = set()
        if request.user.is_authenticated:
            wishlist_service_ids = set(Wishlist.objects.filter(user=request.user).values_list('services_id', flat=True))
        
        return render(request, "app/category.html", {
            "categories": categories,
            "wishlist_service_ids": wishlist_service_ids
        })

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
        
        # Get wishlist items for authenticated users
        wishlist_service_ids = set()
        if request.user.is_authenticated:
            wishlist_service_ids = set(Wishlist.objects.filter(user=request.user).values_list('services_id', flat=True))
        
        return render(request, "app/category.html", {
            "services": services,
            "categories": categories,
            "wishlist_service_ids": wishlist_service_ids
        })
    
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
    
    if not services_id:
        messages.error(request, "Service not specified.")
        return redirect('/services/')
    
    try:
        # Use list() to force evaluation for MongoDB compatibility
        services_list = list(Services.objects.filter(id=services_id))
        if not services_list:
            messages.error(request, "Service not found.")
            return redirect('/services/')
        services = services_list[0]
        
        # Check if item already exists in cart using list()
        cart_items = list(Cart.objects.filter(user=user, services=services))
        
        if cart_items:
            # Item exists - increment quantity using filter + update
            cart_item = cart_items[0]
            new_quantity = (cart_item.quantity or 0) + 1
            Cart.objects.filter(id=cart_item.id).update(quantity=new_quantity)
        else:
            # Item doesn't exist - create new cart entry
            Cart.objects.create(user=user, services=services, quantity=1)
        
    except Exception as e:
        messages.error(request, f"Error adding to cart: {str(e)}")
        return redirect('/services/')
    
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
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)
        
        try:
            # Use list() to force evaluation for MongoDB compatibility
            cart_items = list(Cart.objects.filter(services_id=serv_id, user=request.user))
            
            if not cart_items:
                # Create new cart item
                services_list = list(Services.objects.filter(id=serv_id))
                if not services_list:
                    return JsonResponse({'error': 'Service not found'}, status=404)
                Cart.objects.create(user=request.user, services=services_list[0], quantity=1)
                new_quantity = 1
            else:
                # Update quantity using filter + update for MongoDB
                cart_item = cart_items[0]
                new_quantity = (cart_item.quantity or 0) + 1
                Cart.objects.filter(id=cart_item.id).update(quantity=new_quantity)
            
            # Calculate new totals
            remaining_cart = list(Cart.objects.filter(user=request.user))
            amount = sum(p.quantity * p.services.discounted_price for p in remaining_cart)
            totalamount = amount + 40

            data = {
                'quantity': new_quantity,
                'amount': amount,
                'totalamount': totalamount
            }
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
def minus_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)
        
        try:
            # Use list() to force evaluation for MongoDB compatibility
            cart_items = list(Cart.objects.filter(services_id=serv_id, user=request.user))
            
            if not cart_items:
                return JsonResponse({'error': 'cart item not found'}, status=404)
            
            cart_item = cart_items[0]
            new_quantity = (cart_item.quantity or 1) - 1
            removed = False
            
            if new_quantity <= 0:
                # Delete using filter + delete for MongoDB
                try:
                    Cart.objects.filter(id=cart_item.id).delete()
                except Exception:
                    Cart.objects.filter(services_id=serv_id, user=request.user).delete()
                new_quantity = 0
                removed = True
            else:
                # Update using filter + update for MongoDB
                Cart.objects.filter(id=cart_item.id).update(quantity=new_quantity)
            
            # Calculate new totals
            remaining_cart = list(Cart.objects.filter(user=request.user))
            amount = sum(p.quantity * p.services.discounted_price for p in remaining_cart)
            totalamount = amount + 40

            data = {
                'quantity': new_quantity,
                'amount': amount,
                'totalamount': totalamount,
                'removed': removed
            }
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
def remove_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)

        try:
            # Get cart items for this service and user
            # Use list() to force evaluation to avoid MongoDB cursor issues
            cart_items = list(Cart.objects.filter(services_id=serv_id, user=request.user))
            
            if not cart_items:
                return JsonResponse({'error': 'cart item not found'}, status=404)

            # Sum quantities across any duplicate rows
            removed_quantity = sum((item.quantity or 0) for item in cart_items)
            
            # Delete each item individually to avoid MongoDB queryset delete issues
            for item in cart_items:
                try:
                    Cart.objects.filter(id=item.id).delete()
                except Exception:
                    # Fallback: try deleting by user+services
                    Cart.objects.filter(services_id=serv_id, user=request.user).delete()
                    break

            # Calculate new totals
            user = request.user
            remaining_cart = list(Cart.objects.filter(user=user))
            amount = sum(p.quantity * p.services.discounted_price for p in remaining_cart)
            totalamount = amount + 40

            data = {
                'quantity': removed_quantity,
                'amount': amount,
                'totalamount': totalamount,
                'removed': True
            }
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

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
