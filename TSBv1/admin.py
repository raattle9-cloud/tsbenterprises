from django.contrib import admin
from .models import Customer, Services, Cart, Payment, OrderPlaced

# Register your models here.

@admin.register(Services)
class ServicesModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'discounted_price', 'category', 'service_image']

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name' ,'mobile', 'locality', 'city']

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display=['id', 'user', 'services', 'quantity']

@admin.register(Payment)
class PaymentModelAdmin(admin.ModelAdmin):
    list_display=['id', 'user', 'amount', 'razorpay_order_id', 'razorpay_payment_status', 'razorpay_payment_id', 'paid']

@admin.register(OrderPlaced)
class OrderPlacedModelAdmin(admin.ModelAdmin):
    list_display=['id', 'user', 'customer', 'services', 'quantity', 'ordered_date', 'status','payment']