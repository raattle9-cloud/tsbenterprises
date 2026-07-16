from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import reverse, path
from django.http import HttpResponseRedirect, Http404
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.template.response import TemplateResponse
from .models import Customer, Services, Cart, Payment, OrderPlaced, ServiceImage, AdvanceBooking, HeroImage, TrustedPartner, Invoice

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
    list_display = ['id', 'title', 'discounted_price', 'selling_price', 'category', 'vendor_whatsapp', 'supports_advance_payment', 'primary_image_preview', 'delete_button']
    list_filter = ['category', 'supports_advance_payment']
    search_fields = ['title', 'description']
    list_editable = ['discounted_price', 'selling_price', 'category']
    readonly_fields = ['id', 'delete_button']
    ordering = ()
    inlines = [ServiceImageInline]
    actions = ['delete_selected_services']
    
    class Media:
        js = ('app/js/admin_service.js',)
    
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
        ('Vendor Contact', {
            'fields': ('vendor_whatsapp',),
            'description': 'WhatsApp number of the vendor. Notifications will be sent here when a customer purchases this service.'
        }),
    )

    def primary_image_preview(self, obj):
        image = obj.get_primary_image()
        if image:
            url = image.image_url or image.image.url if image.image else ''
            return mark_safe(f'<img src="{url}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 6px;" />')
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


@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_preview', 'alt_text', 'display_order', 'is_active', 'uploaded_at', 'delete_button']
    list_editable = ['alt_text', 'display_order', 'is_active']
    readonly_fields = ['id', 'image_preview_large', 'uploaded_at']
    ordering = ()
    actions = ['activate_images', 'deactivate_images', 'delete_selected_images']
    change_list_template = 'admin/hero_image_changelist.html'

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []

    fieldsets = (
        ('Image', {
            'fields': ('image', 'image_preview_large')
        }),
        ('Settings', {
            'fields': ('alt_text', 'display_order', 'is_active')
        }),
        ('Info', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='heroimage_bulk_upload'),
        ]
        return custom_urls + super().get_urls()

    def bulk_upload_view(self, request):
        from django.contrib import messages
        if request.method == 'POST':
            files = request.FILES.getlist('images')
            if not files:
                messages.warning(request, 'No files selected.')
                return HttpResponseRedirect(reverse('admin:TSBv1_heroimage_changelist'))
            count = 0
            # Get the highest current display_order
            existing = list(HeroImage.objects.all())
            max_order = max([img.display_order for img in existing], default=0) if existing else 0
            for f in files:
                max_order += 1
                HeroImage.objects.create(
                    image=f,
                    alt_text=f.name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
                    display_order=max_order,
                    is_active=True,
                )
                count += 1
            messages.success(request, f'Successfully uploaded {count} hero image(s).')
            return HttpResponseRedirect(reverse('admin:TSBv1_heroimage_changelist'))
        context = {
            **self.admin_site.each_context(request),
            'title': 'Bulk Upload Hero Images',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/hero_image_bulk_upload.html', context)

    def image_preview(self, obj):
        if obj.image:
            url = obj.image_url or obj.image.url
            return mark_safe(f'<img src="{url}" style="width: 120px; height: 60px; object-fit: cover; border-radius: 6px;" />')
        return "-"
    image_preview.short_description = 'Preview'

    def image_preview_large(self, obj):
        if obj.image:
            url = obj.image_url or obj.image.url
            return mark_safe(f'<img src="{url}" style="max-width: 400px; max-height: 200px; object-fit: cover; border-radius: 8px;" />')
        return "No image uploaded"
    image_preview_large.short_description = 'Image Preview'

    def delete_button(self, obj):
        if obj.pk:
            delete_url = reverse('admin:TSBv1_heroimage_delete', args=[obj.pk])
            return mark_safe(
                f'<a href="{delete_url}" class="button" style="background-color: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">'
                f'<i class="fas fa-trash"></i> Delete'
                f'</a>'
            )
        return "-"
    delete_button.short_description = 'Actions'
    delete_button.allow_tags = True

    def activate_images(self, request, queryset):
        count = queryset.count()
        for img in queryset:
            HeroImage.objects.filter(id=img.id).update(is_active=True)
        self.message_user(request, f'{count} image(s) activated.')
    activate_images.short_description = 'Activate selected images'

    def deactivate_images(self, request, queryset):
        count = queryset.count()
        for img in queryset:
            HeroImage.objects.filter(id=img.id).update(is_active=False)
        self.message_user(request, f'{count} image(s) deactivated.')
    deactivate_images.short_description = 'Deactivate selected images'

    def delete_selected_images(self, request, queryset):
        count = queryset.count()
        for img in queryset:
            img.delete()
        self.message_user(request, f'Successfully deleted {count} hero image(s).')
    delete_selected_images.short_description = 'Delete selected hero images'

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error deleting hero image: {str(e)}')

    def delete_queryset(self, request, queryset):
        count = queryset.count()
        for img in queryset:
            try:
                img.delete()
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error deleting hero image {img.id}: {str(e)}')
        from django.contrib import messages
        messages.success(request, f'Successfully deleted {count} hero image(s).')

    def get_object(self, request, object_id, from_field=None):
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        try:
            object_id = field.to_python(object_id)
            obj = queryset.get(pk=object_id)
        except (model.DoesNotExist, ValidationError, ValueError):
            return None
        return obj


@admin.register(TrustedPartner)
class TrustedPartnerAdmin(admin.ModelAdmin):
    list_display = ['id', 'logo_preview', 'name', 'website_url', 'display_order', 'is_active', 'uploaded_at', 'delete_button']
    list_editable = ['name', 'display_order', 'is_active']
    readonly_fields = ['id', 'logo_preview_large', 'uploaded_at']
    ordering = ()
    actions = ['activate_partners', 'deactivate_partners', 'delete_selected_partners']
    change_list_template = 'admin/trusted_partner_changelist.html'

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()

    def get_sortable_by(self, request):
        return []

    fieldsets = (
        ('Logo', {
            'fields': ('logo', 'logo_preview_large')
        }),
        ('Settings', {
            'fields': ('name', 'website_url', 'display_order', 'is_active')
        }),
        ('Info', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='trustedpartner_bulk_upload'),
        ]
        return custom_urls + super().get_urls()

    def bulk_upload_view(self, request):
        from django.contrib import messages
        if request.method == 'POST':
            files = request.FILES.getlist('logos')
            if not files:
                messages.warning(request, 'No files selected.')
                return HttpResponseRedirect(reverse('admin:TSBv1_trustedpartner_changelist'))
            count = 0
            existing = list(TrustedPartner.objects.all())
            max_order = max([p.display_order for p in existing], default=0) if existing else 0
            for f in files:
                max_order += 1
                TrustedPartner.objects.create(
                    logo=f,
                    name=f.name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
                    display_order=max_order,
                    is_active=True,
                )
                count += 1
            messages.success(request, f'Successfully uploaded {count} partner logo(s).')
            return HttpResponseRedirect(reverse('admin:TSBv1_trustedpartner_changelist'))
        context = {
            **self.admin_site.each_context(request),
            'title': 'Bulk Upload Partner Logos',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/trusted_partner_bulk_upload.html', context)

    def logo_preview(self, obj):
        if obj.logo:
            url = obj.logo_url or obj.logo.url
            return mark_safe(f'<img src="{url}" style="width: 80px; height: 50px; object-fit: contain; border-radius: 6px; background: #f5f5f5; padding: 4px;" />')
        return "-"
    logo_preview.short_description = 'Preview'

    def logo_preview_large(self, obj):
        if obj.logo:
            url = obj.logo_url or obj.logo.url
            return mark_safe(f'<img src="{url}" style="max-width: 300px; max-height: 150px; object-fit: contain; border-radius: 8px; background: #f5f5f5; padding: 8px;" />')
        return "No logo uploaded"
    logo_preview_large.short_description = 'Logo Preview'

    def delete_button(self, obj):
        if obj.pk:
            delete_url = reverse('admin:TSBv1_trustedpartner_delete', args=[obj.pk])
            return mark_safe(
                f'<a href="{delete_url}" class="button" style="background-color: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">'
                f'<i class="fas fa-trash"></i> Delete'
                f'</a>'
            )
        return "-"
    delete_button.short_description = 'Actions'
    delete_button.allow_tags = True

    def activate_partners(self, request, queryset):
        count = queryset.count()
        for p in queryset:
            TrustedPartner.objects.filter(id=p.id).update(is_active=True)
        self.message_user(request, f'{count} partner(s) activated.')
    activate_partners.short_description = 'Activate selected partners'

    def deactivate_partners(self, request, queryset):
        count = queryset.count()
        for p in queryset:
            TrustedPartner.objects.filter(id=p.id).update(is_active=False)
        self.message_user(request, f'{count} partner(s) deactivated.')
    deactivate_partners.short_description = 'Deactivate selected partners'

    def delete_selected_partners(self, request, queryset):
        count = queryset.count()
        for p in queryset:
            p.delete()
        self.message_user(request, f'Successfully deleted {count} partner(s).')
    delete_selected_partners.short_description = 'Delete selected partners'

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error deleting partner: {str(e)}')

    def delete_queryset(self, request, queryset):
        count = queryset.count()
        for p in queryset:
            try:
                p.delete()
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error deleting partner {p.id}: {str(e)}')
        from django.contrib import messages
        messages.success(request, f'Successfully deleted {count} partner(s).')

    def get_object(self, request, object_id, from_field=None):
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        try:
            object_id = field.to_python(object_id)
            obj = queryset.get(pk=object_id)
        except (model.DoesNotExist, ValidationError, ValueError):
            return None
        return obj


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_no', 'customer', 'service', 'amount', 'created_at', 'download_link']
    list_filter = ['created_at']
    search_fields = ['invoice_no', 'customer__name', 'service__title']
    readonly_fields = ['invoice_no', 'token', 'created_at', 'download_link']
    ordering = ()

    def download_link(self, obj):
        url = obj.get_download_url()
        return mark_safe(f'<a href="{url}" target="_blank">Download PDF</a>')
    download_link.short_description = 'Invoice PDF'

    def get_ordering(self, request):
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).order_by()
