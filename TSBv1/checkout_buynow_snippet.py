def checkout_buynow(request, service_id):
    """
    Handle 'Buy Now' - add item to cart and show checkout page with Razorpay integration.
    Mimics show_cart logic but for the checkout page.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to proceed.")
        return redirect('customerlogin') # Or login page

    try:
        service = Services.objects.get(id=service_id)
        # Check if already in cart
        existing_cart = Cart.objects.filter(user=request.user, services=service)
        if not existing_cart.exists():
            Cart.objects.create(user=request.user, services=service, quantity=1)
        # If exists, we leave it (or update quantity? leaving it is standard)
    except Services.DoesNotExist:
        messages.error(request, "Service not found.")
        return redirect('services')

    # --- Prepare Checkout Data (Same as show_cart) ---
    user = request.user
    cart = Cart.objects.filter(user=user).select_related('services')
    
    totalamount = 0
    advance_amount = 0
    
    for p in cart:
        item_total = p.quantity * p.services.discounted_price
        totalamount += item_total
        
        if p.services.supports_advance_payment:
            item_advance = p.services.calculate_advance_amount(p.quantity)
        else:
            item_advance = item_total
        
        advance_amount += item_advance
    
    totalamount = int(totalamount)
    advance_amount = int(advance_amount)
    remaining_amount = totalamount - advance_amount
    
    razoramount = int(advance_amount * 100)
    
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
            
    # Fetch customer profiles
    customers = Customer.objects.filter(user=request.user)

    context = {
        'cart': cart,
        'amount': totalamount, # Subtotal (same as total here for simplicity unless broken out)
        'total_amount': totalamount, # Display total
        'advance_amount': advance_amount,
        'remaining_amount': remaining_amount,
        'razoramount': razoramount,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key_id': razorpay_key_id,
        'currency': 'INR',
        'customers': customers,
    }
    
    return render(request, 'app/checkout.html', context)
