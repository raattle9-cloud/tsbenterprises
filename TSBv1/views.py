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
from django.utils import timezone


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


def portal_hub(request):
    """
    Unified portal hub for all user types - provides quick access to all portals
    """
    context = {
        'is_admin': request.user.is_superuser if request.user.is_authenticated else False,
        'is_staff': request.user.is_staff if request.user.is_authenticated else False,
    }
    
    # Add quick stats for staff/admin users
    if request.user.is_authenticated and request.user.is_staff:
        from django.utils import timezone
        from .models import AdvanceBooking
        from django.db.models import Sum
        
        today = timezone.now().date()
        
        # Get all bookings and filter in Python to avoid MongoDB date issues
        all_bookings = list(AdvanceBooking.objects.all())
        
        pending_today = 0
        verified_today = 0
        revenue_today = 0.0
        
        for booking in all_bookings:
            if str(booking.booking_date) == str(today):
                if booking.status == 'PENDING':
                    pending_today += 1
                elif booking.status in ['VERIFIED', 'USED']:
                    verified_today += 1
                    try:
                        revenue_today += float(str(booking.total_amount))
                    except:
                        pass
        
        context['stats'] = {
            'pending_today': pending_today,
            'verified_today': verified_today,
            'revenue_today': revenue_today,
            'total_bookings': len(all_bookings),
        }
    
    return render(request, 'app/portal_hub.html', context)


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
            try:
                form.save()
                messages.success(request, "Congratulations! You have successfully registered.")
                form = CustomerRegistrationForm()
            except Exception as e:
                import traceback
                print(f"Registration error: {e}")
                print(traceback.format_exc())
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            messages.error(request, "Registration failed. Please check your input and try again.")

        return render(request, "app/customerregistration.html",locals())
    
#Customer Login Logic
class CustomerLoginview(View):
    def get(self, request):
        return render(request, "app/customerlogin.html",locals())
    
    def post(self, request):
        return render(request, "app/customerlogin.html",locals())
    
class ProfileView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('customerlogin')
        
        # Try to get existing customer data for this user
        existing_customers = list(Customer.objects.filter(user=request.user))
        
        if existing_customers:
            # Pre-populate form with existing data
            customer = existing_customers[0]
            initial_data = {
                'name': customer.name,
                'locality': customer.locality,
                'city': customer.city,
                'mobile': customer.mobile,
                'state': customer.state,
                'zipcode': customer.zipcode,
            }
            form = CustomerProfileForm(initial=initial_data)
            has_profile = True
        else:
            form = CustomerProfileForm()
            has_profile = False
        
        return render(request, "app/profile.html", {'form': form, 'has_profile': has_profile})
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('customerlogin')
        
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']
            
            # Check if customer already exists for this user
            existing_customers = list(Customer.objects.filter(user=user))
            
            if existing_customers:
                # Update existing customer using filter().update() for MongoDB compatibility
                Customer.objects.filter(user=user).update(
                    name=name,
                    locality=locality,
                    city=city,
                    mobile=mobile,
                    state=state,
                    zipcode=zipcode
                )
                messages.success(request, "Profile Updated Successfully!")
            else:
                # Create new customer
                reg = Customer(user=user, name=name, locality=locality, city=city, mobile=mobile, state=state, zipcode=zipcode)
                reg.save()
                messages.success(request, "Profile Saved Successfully!")
            
            has_profile = True
        else:
            messages.warning(request, "Invalid Input Data!")
            has_profile = len(list(Customer.objects.filter(user=request.user))) > 0
        
        return render(request, "app/profile.html", {'form': form, 'has_profile': has_profile})

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
    
    totalamount = 0
    advance_amount = 0
    
    # Calculate totals and advance amounts for each cart item
    for p in cart:
        item_total = p.quantity * p.services.discounted_price
        totalamount += item_total
        
        # Use the service's configured advance payment settings
        if p.services.supports_advance_payment:
            item_advance = p.services.calculate_advance_amount(p.quantity)
        else:
            # For services without advance payment config, require full payment
            item_advance = item_total
        
        advance_amount += item_advance
    
    # Convert to integers for display
    totalamount = int(totalamount)
    advance_amount = int(advance_amount)
    remaining_amount = totalamount - advance_amount
    
    # Convert advance amount to paise for Razorpay
    razoramount = int(advance_amount * 100)
    
    # Create Razorpay order for the advance amount only
    razorpay_order_id = None
    razorpay_key_id = None
    
    if cart and advance_amount > 0:
        try:
            client = razorpay.Client(auth=(settings.RAZOR_PAY_KEY_ID, settings.RAZOR_PAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': razoramount,
                'currency': 'INR',
                'receipt': f'cart_{user.id}_{int(timezone.now().timestamp())}',
                'payment_capture': 1
            })
            razorpay_order_id = razorpay_order['id']
            razorpay_key_id = settings.RAZOR_PAY_KEY_ID
        except Exception as e:
            print(f"Razorpay order creation failed: {e}")
    
    context = {
        'cart': cart,
        'amount': totalamount,
        'totalamount': totalamount,
        'advance_amount': advance_amount,
        'remaining_amount': remaining_amount,
        'razoramount': razoramount,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key_id': razorpay_key_id,
        'currency': 'INR',
    }
    return render(request, 'app/addtocart.html', context)

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
        # Handle "Buy Now" - automatically add item to cart if buy_now parameter is present
        buy_now_id = request.GET.get('buy_now')
        if buy_now_id and request.user.is_authenticated:
            try:
                service = Services.objects.get(id=buy_now_id)
                # Check if already in cart
                existing_cart = Cart.objects.filter(user=request.user, services=service)
                if not existing_cart.exists():
                    # Add to cart with quantity 1
                    Cart.objects.create(user=request.user, services=service, quantity=1)
                
                # Redirect to clean URL to avoid re-adding on refresh and show clean address
                return redirect('checkout')
            except Services.DoesNotExist:
                pass  # Service not found, just continue to checkout
        
        # Fetch cart items for display
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user)
            amount = 0.0
            for p in cart:
                value = p.quantity * p.services.discounted_price
                amount = amount + value
            total_amount = amount + 40 # Adding GST/Shipping as per template placeholder
        else:
            cart = []
            total_amount = 0

        return render(request, 'app/checkout.html', locals())

def plus_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        serv_id = request.GET.get('serv_id') or request.GET.get('prod_id')
        if not serv_id:
            return JsonResponse({'error': 'missing serv_id or prod_id'}, status=400)
        
        try:
            # Get the service object first for safe filtering
            services_list = list(Services.objects.filter(id=serv_id))
            if not services_list:
                return JsonResponse({'error': 'Service not found'}, status=404)
            service_obj = services_list[0]

            # Use the object for filtering
            cart_items = list(Cart.objects.filter(services=service_obj, user=request.user))
            
            if not cart_items:
                # Create new cart item
                Cart.objects.create(user=request.user, services=service_obj, quantity=1)
                new_quantity = 1
            else:
                # Update quantity using filter + update for MongoDB
                cart_item = cart_items[0]
                new_quantity = (cart_item.quantity or 0) + 1
                Cart.objects.filter(id=cart_item.id).update(quantity=new_quantity)
            
            # Calculate new totals
            remaining_cart = list(Cart.objects.filter(user=request.user))
            amount = sum(p.quantity * p.services.discounted_price for p in remaining_cart)
            totalamount = amount

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
            # Get the service object first
            services_list = list(Services.objects.filter(id=serv_id))
            if not services_list:
                return JsonResponse({'error': 'Service not found'}, status=404)
            service_obj = services_list[0]

            # Use the object for filtering
            cart_items = list(Cart.objects.filter(services=service_obj, user=request.user))
            
            if not cart_items:
                return JsonResponse({'error': 'cart item not found'}, status=404)
            
            cart_item = cart_items[0]
            new_quantity = (cart_item.quantity or 1) - 1
            removed = False
            
            if new_quantity <= 0:
                try:
                    cart_item.delete()
                except Exception:
                    Cart.objects.filter(id=cart_item.id).delete()
                new_quantity = 0
                removed = True
            else:
                # Update using filter + update for MongoDB
                Cart.objects.filter(id=cart_item.id).update(quantity=new_quantity)
            
            # Calculate new totals
            remaining_cart = list(Cart.objects.filter(user=request.user))
            amount = sum(p.quantity * p.services.discounted_price for p in remaining_cart)
            totalamount = amount

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
            # Get the service object first
            services_list = list(Services.objects.filter(id=serv_id))
            if not services_list:
                return JsonResponse({'error': 'Service not found'}, status=404)
            service_obj = services_list[0]

            # Get cart items for this service and user using object filter
            cart_items = list(Cart.objects.filter(services=service_obj, user=request.user))
            
            if not cart_items:
                return JsonResponse({'error': 'cart item not found'}, status=404)

            # Sum quantities across any duplicate rows
            removed_quantity = sum((item.quantity or 0) for item in cart_items)
            
            # Delete each item individually
            # Direct object deletion is more reliable in Djongo/MongoDB
            for item in cart_items:
                try:
                    item.delete()
                except Exception:
                    # Final fallback using filter
                    Cart.objects.filter(id=item.id).delete()

            # Calculate new totals
            user = request.user
            remaining_cart = list(Cart.objects.filter(user=user))
            amount = sum(p.quantity * p.services.discounted_price for p in remaining_cart)
            totalamount = amount

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
