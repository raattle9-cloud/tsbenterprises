from django.contrib import admin
from django.utils.html import mark_safe
from .models import Customer, Services, Cart, Payment, OrderPlaced, ServiceImage

# Register your models here.

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 4
    min_num = 1
    max_num = 4
    validate_min = True
    validate_max = True


@admin.register(Services)
class ServicesModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'discounted_price', 'selling_price', 'category', 'primary_image_preview']
    list_filter = ['category']
    search_fields = ['title', 'description']
    list_editable = ['discounted_price', 'selling_price', 'category']
    readonly_fields = ['id']
    inlines = [ServiceImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category')
        }),
        ('Pricing', {
            'fields': ('selling_price', 'discounted_price')
        }),
        ('Details', {
            'fields': ('description', 'composition', 'servapp')
        }),
    )

    def primary_image_preview(self, obj):
        image = obj.get_primary_image()
        if image:
            return mark_safe(f'<img src="{image.image.url}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 6px;" />')
        return "-"

    primary_image_preview.short_description = 'Primary Image'

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'mobile', 'city', 'state', 'zipcode']
    list_filter = ['state', 'city']
    search_fields = ['name', 'mobile', 'user__username', 'user__email', 'locality', 'city']
    readonly_fields = ['id']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name')
        }),
        ('Contact Details', {
            'fields': ('mobile',)
        }),
        ('Address', {
            'fields': ('locality', 'city', 'state', 'zipcode')
        }),
    )

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'services', 'quantity', 'total_cost']
    list_filter = ['services__category']
    search_fields = ['user__username', 'services__title']
    readonly_fields = ['id', 'total_cost']
    list_editable = ['quantity']

@admin.register(Payment)
class PaymentModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'paid', 'razorpay_order_id', 'razorpay_payment_status', 'razorpay_payment_id']
    list_filter = ['paid', 'razorpay_payment_status']
    search_fields = ['user__username', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['id']
    list_editable = ['paid']

@admin.register(OrderPlaced)
class OrderPlacedModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'services', 'quantity', 'status', 'ordered_date', 'total_cost']
    list_filter = ['status', 'ordered_date', 'services__category']
    search_fields = ['user__username', 'services__title', 'customer__name']
    readonly_fields = ['id', 'ordered_date', 'total_cost']
    list_editable = ['status']
    date_hierarchy = 'ordered_date'