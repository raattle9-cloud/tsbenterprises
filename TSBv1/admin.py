from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from .models import Customer, Services, Cart, Payment, OrderPlaced, ServiceImage, AdvanceBooking

# Register your models here.

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 4
    min_num = 1
    max_num = 4
    validate_min = True
    validate_max = True
    ordering = ()

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()


@admin.register(Services)
class ServicesModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'discounted_price', 'selling_price', 'category', 'supports_advance_payment', 'primary_image_preview', 'delete_button']
    list_filter = ['category', 'supports_advance_payment']
    search_fields = ['title', 'description']
    list_editable = ['discounted_price', 'selling_price', 'category']
    readonly_fields = ['id', 'delete_button']
    ordering = ()
    inlines = [ServiceImageInline]
    actions = ['delete_selected_services']
    
    def delete_button(self, obj):
        """Add a delete button for each service"""
        if obj.pk:
            delete_url = reverse('admin:TSBv1_services_delete', args=[obj.pk])
            return mark_safe(
                f'<a href="{delete_url}" class="button" style="background-color: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">'
                f'<i class="fas fa-trash"></i> Delete'
                f'</a>'
            )
        return "-"
    delete_button.short_description = 'Actions'
    delete_button.allow_tags = True
    
    def delete_selected_services(self, request, queryset):
        """Custom delete action with confirmation"""
        count = queryset.count()
        for service in queryset:
            # Delete associated images first
            service.images.all().delete()
            service.delete()
        self.message_user(request, f'Successfully deleted {count} service(s) and their associated images.')
    delete_selected_services.short_description = 'Delete selected services'

    def get_ordering(self, request):
        return [] # No ordering to avoid Djongo errors

    def get_queryset(self, request):
        return super().get_queryset(request).order_by() # Explicitly remove any default ordering

    def get_sortable_by(self, request):
        return [] # Disable column header sorting
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category')
        }),
        ('Pricing', {
            'fields': ('selling_price', 'discounted_price')
        }),
        ('Advance Payment (for Waterparks)', {
            'fields': ('supports_advance_payment', 'advance_payment_type', 'advance_payment_value'),
            'description': 'Enable advance payment option for this service. Customers can pay partially online and complete payment at the venue.'
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
    
    def delete_model(self, request, obj):
        """Override delete_model to handle MongoDB/Djongo hashing issues"""
        try:
            # Delete associated images first
            obj.images.all().delete()
            # Delete the service
            obj.delete()
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error deleting service: {str(e)}')
    
    def delete_queryset(self, request, queryset):
        """Override delete_queryset for bulk delete operations"""
        count = queryset.count()
        for service in queryset:
            try:
                # Delete associated images first
                service.images.all().delete()
                # Delete the service
                service.delete()
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error deleting service {service.id}: {str(e)}')
        from django.contrib import messages
        messages.success(request, f'Successfully deleted {count} service(s) and their associated images.')
    
    def get_object(self, request, object_id, from_field=None):
        """Override get_object to avoid hashing issues with MongoDB"""
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        try:
            object_id = field.to_python(object_id)
            obj = queryset.get(pk=object_id)
        except (model.DoesNotExist, ValidationError, ValueError):
            return None
        return obj
    
    def delete_view(self, request, object_id, extra_context=None):
        """Override delete_view to handle MongoDB/Djongo hashing issues"""
        from django.contrib.admin.options import IS_POPUP_VAR
        from django.contrib import messages
        from django.template.response import TemplateResponse
        
        # Get the object
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            raise Http404('%(name)s object with primary key %(key)r does not exist.' % {
                'name': self.model._meta.verbose_name,
                'key': unquote(object_id),
            })
        
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        
        if request.method == 'POST':
            # Handle the actual deletion
            try:
                # Store title before deletion
                service_title = str(obj)
                # Delete associated images first
                obj.images.all().delete()
                # Delete the service
                obj.delete()
                messages.success(request, f'Service "{service_title}" was deleted successfully.')
            except Exception as e:
                messages.error(request, f'Error deleting service: {str(e)}')
            
            # Redirect after deletion
            if IS_POPUP_VAR in request.POST:
                return HttpResponseRedirect(request.POST.get('next', '/admin/'))
            return HttpResponseRedirect(reverse('admin:TSBv1_services_changelist'))
        
        # Show confirmation page
        opts = self.model._meta
        app_label = opts.app_label
        
        context = {
            **self.admin_site.each_context(request),
            'title': f'Delete {opts.verbose_name}',
            'object_name': str(opts.verbose_name),
            'object': obj,
            'opts': opts,
            'app_label': app_label,
            'has_delete_permission': self.has_delete_permission(request, obj),
            'original': obj,
            **(extra_context or {}),
        }
        
        return TemplateResponse(
            request,
            self.delete_confirmation_template or [
                "admin/%s/%s/delete_confirmation.html" % (app_label, opts.model_name),
                "admin/%s/delete_confirmation.html" % app_label,
                "admin/delete_confirmation.html"
            ],
            context,
        )

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'mobile', 'city', 'state', 'zipcode']
    list_filter = ['state', 'city']
    search_fields = ['name', 'mobile', 'user__username', 'user__email', 'locality', 'city']
    readonly_fields = ['id']
    ordering = ()

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []

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
    ordering = ()
    readonly_fields = ['id', 'total_cost']
    list_editable = ['quantity']

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []

@admin.register(Payment)
class PaymentModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'paid', 'razorpay_order_id', 'razorpay_payment_status', 'razorpay_payment_id']
    list_filter = ['paid', 'razorpay_payment_status']
    search_fields = ['user__username', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['id']
    ordering = ()
    list_editable = ['paid']

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []

@admin.register(OrderPlaced)
class OrderPlacedModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'services', 'quantity', 'status', 'ordered_date', 'is_advance_order', 'total_cost']
    list_filter = ['status', 'ordered_date', 'services__category', 'is_advance_order']
    search_fields = ['user__username', 'services__title', 'customer__name']
    ordering = ()
    readonly_fields = ['id', 'ordered_date', 'total_cost']
    list_editable = ['status']

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []


@admin.register(AdvanceBooking)
class AdvanceBookingAdmin(admin.ModelAdmin):
    list_display = ['booking_code', 'customer_name', 'service', 'booking_date', 'status', 'total_amount', 'advance_paid', 'remaining_amount', 'created_at', 'verified_at']
    list_filter = ['status', 'booking_date', 'service', 'created_at']
    search_fields = ['booking_code', 'customer__name', 'user__username', 'user__email', 'service__title']
    ordering = ()
    readonly_fields = ['booking_code', 'qr_hash', 'created_at', 'verified_at', 'qr_code_preview', 'verification_attempts']
    
    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []

    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_code', 'status', 'booking_date', 'qr_code_preview')
        }),
        ('Customer & Service', {
            'fields': ('user', 'customer', 'service', 'quantity')
        }),
        ('Payment Details', {
            'fields': ('total_amount', 'advance_paid', 'remaining_amount', 'advance_payment', 'final_payment')
        }),
        ('Verification', {
            'fields': ('verified_at', 'verified_by_staff', 'verification_ip', 'verification_attempts'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'valid_until'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('qr_hash',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['cancel_bookings', 'mark_as_verified']
    
    def customer_name(self, obj):
        return obj.customer.name
    customer_name.short_description = 'Customer'
    
    def qr_code_preview(self, obj):
        if obj.qr_code_data:
            return mark_safe(f'<img src="{obj.qr_code_data}" style="width: 200px; height: 200px;" />')
        return "QR Code not generated yet"
    qr_code_preview.short_description = 'QR Code'
    
    def cancel_bookings(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(status='CANCELLED')
        self.message_user(request, f'{updated} booking(s) cancelled successfully.')
    cancel_bookings.short_description = 'Cancel selected bookings'
    
    def mark_as_verified(self, request, queryset):
        from django.utils import timezone
        for booking in queryset.filter(status='PENDING'):
            booking.status = 'VERIFIED'
            booking.verified_at = timezone.now()
            booking.verified_by_staff = f"Admin: {request.user.username}"
            booking.save()
        self.message_user(request, f'{queryset.count()} booking(s) marked as verified.')
    mark_as_verified.short_description = 'Mark as verified (manual)'
