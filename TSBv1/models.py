from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Create your models here.


class MongoFloatField(models.FloatField):
    """Custom FloatField that handles MongoDB's Decimal128 type"""
    
    def from_db_value(self, value, expression, connection):
        """Convert Decimal128 from MongoDB to Python float"""
        if value is None:
            return value
        # Handle Decimal128 objects from MongoDB
        try:
            return float(value)
        except (TypeError, ValueError):
            # If it's a Decimal128, convert via string
            try:
                return float(str(value))
            except (TypeError, ValueError):
                return 0.0
    
    def get_prep_value(self, value):
        """Prepare value for database storage"""
        if value is None:
            return value
        # Convert any type to float before saving
        try:
            if isinstance(value, (int, float)):
                return float(value)
            else:
                # Handle Decimal128, Decimal, or string
                return float(str(value))
        except (TypeError, ValueError):
            return 0.0

CATEGORY_CHOICES = (
    ("RE", "Resort"),
    ("WP", "Waterpark"),
    ("DP", "Destination_packages"),
    ("DB", "Dhaba"),
    ("VI", "Villas"),
    ("GO", "Game_On"),
)
STATE_CHOICES = (
    ("AN", "Andaman and Nicobar Islands"),
    ("AP", "Andhra Pradesh"),
    ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"),
    ("BR", "Bihar"),
    ("CG", "Chhattisgarh"),
    ("CH", "Chandigarh"),
    ("DN", "Dadra and Nagar Haveli"),
    ("DD", "Daman and Diu"),
    ("DL", "Delhi"),
    ("GA", "Goa"),
    ("GJ", "Gujarat"),
    ("HR", "Haryana"),
    ("HP", "Himachal Pradesh"),
    ("JK", "Jammu and Kashmir"),
    ("JH", "Jharkhand"),
    ("KA", "Karnataka"),
    ("KL", "Kerala"),
    ("LA", "Ladakh"),
    ("LD", "Lakshadweep"),
    ("MP", "Madhya Pradesh"),
    ("MH", "Maharashtra"),
    ("MN", "Manipur"),
    ("ML", "Meghalaya"),
    ("MZ", "Mizoram"),
    ("NL", "Nagaland"),
    ("OD", "Odisha"),
    ("PB", "Punjab"),
    ("PY", "Pondicherry"),
    ("RJ", "Rajasthan"),
    ("SK", "Sikkim"),
    ("TN", "Tamil Nadu"),
    ("TS", "Telangana"),
    ("TR", "Tripura"),
    ("UP", "Uttar Pradesh"),
    ("UK", "Uttarakhand"),
    ("WB", "West Bengal"),
)


class Services(models.Model):
    title = models.CharField(max_length=100)
    selling_price = MongoFloatField()
    discounted_price = MongoFloatField()
    description = models.TextField()
    composition = models.TextField(default="")
    servapp = models.TextField(default="")
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)

    # Advance Payment Fields (for Waterparks)
    supports_advance_payment = models.BooleanField(default=False)
    advance_payment_type = models.CharField(
        max_length=10,
        choices=(("FIXED", "Fixed Amount"), ("PERCENTAGE", "Percentage")),
        default="FIXED",
        blank=True,
    )
    advance_payment_value = MongoFloatField(
        default=0,
        help_text="Fixed amount in INR or percentage (0-100)",
    )

    # Vendor Contact
    vendor_whatsapp = models.CharField(
        max_length=15,
        blank=True,
        default="",
        help_text="Vendor WhatsApp number in international format (digits only, e.g. 919876543210)",
    )

    def __str__(self):
        return self.title

    def get_primary_image(self):
        # Fetch all related images without any SQL-level ordering or limiting
        images_qs = self.images.all()
        # Convert to list to avoid further DB hits and take the first one in Python
        images_list = list(images_qs)
        return images_list[0] if images_list else None

    def get_primary_image_url(self):
        image = self.get_primary_image()
        if image and image.image:
            return image.image.url
        return ""

    def calculate_advance_amount(self, quantity=1):
        """Calculate advance payment amount based on type"""
        if not self.supports_advance_payment:
            return 0

        total_price = self.discounted_price * quantity

        # Convert advance_payment_value to float
        # MongoDB's Decimal128 requires conversion via string representation
        advance_value = self.advance_payment_value

        # Always convert via string to handle Decimal128 (MongoDB), Decimal, and other types
        try:
            # Try direct conversion first for standard types
            if isinstance(advance_value, (int, float)):
                advance_value = float(advance_value)
            else:
                # For Decimal128, Decimal, or any other type, convert via string
                advance_value = float(str(advance_value))
        except (ValueError, TypeError):
            # Ultimate fallback: default to 0 if conversion fails
            advance_value = 0.0

        if self.advance_payment_type == "PERCENTAGE":
            return (total_price * advance_value) / 100
        else:  # FIXED
            return advance_value * quantity


class ServiceImage(models.Model):
    service = models.ForeignKey(
        Services, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="service/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service.title} image"

    @property
    def image_url(self):
        """
        Returns the correct image URL:
        - Cloudinary URL if the image was uploaded to Cloudinary
        - Local static URL if the image is stored locally
        """
        if not self.image:
            return ""

        image_path = str(self.image)

        # If it's already a full URL (Cloudinary), return it
        if image_path.startswith("http"):
            return image_path

        # Check if the image exists on Cloudinary by checking if the URL is a Cloudinary URL
        try:
            url = self.image.url
            if "cloudinary.com" in url:
                return url
        except Exception:
            pass

        # Fallback to local static URL for existing local images
        # Images are stored in static/images/service/
        from django.conf import settings

        return f"{settings.STATIC_URL}images/{image_path}"


class HeroImage(models.Model):
    image = models.ImageField(upload_to="hero/")
    alt_text = models.CharField(max_length=200, default="Hero slide")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hero Image {self.id} - {self.alt_text}"

    @property
    def image_url(self):
        if not self.image:
            return ""

        image_path = str(self.image)

        if image_path.startswith("http"):
            return image_path

        try:
            url = self.image.url
            if "cloudinary.com" in url:
                return url
        except Exception:
            pass

        from django.conf import settings
        return f"{settings.STATIC_URL}images/{image_path}"


class TrustedPartner(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="partners/")
    website_url = models.URLField(blank=True, default="")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def logo_url(self):
        if not self.logo:
            return ""

        logo_path = str(self.logo)

        if logo_path.startswith("http"):
            return logo_path

        try:
            url = self.logo.url
            if "cloudinary.com" in url:
                return url
        except Exception:
            pass

        from django.conf import settings
        return f"{settings.STATIC_URL}images/{logo_path}"


class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=20)
    mobile = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="Mobile number must be 10 digits",
                code="invalid_mobile",
            ),
        ],
    )
    zipcode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES, max_length=100)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    services = models.ForeignKey(Services, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_cost(self):
        return self.quantity * self.services.discounted_price


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    services = models.ForeignKey(Services, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "services")

    def __str__(self):
        return f"{self.user.username} - {self.services.title}"


# Payment models
STATUS_CHOICES = (
    ("SUCCESS", "SUCCESS"),
    ("PENDING", "PENDING"),
    ("FAILED", "FAILED"),
)

PAYMENT_TYPE_CHOICES = (
    ("FULL", "Full Payment"),
    ("ADVANCE", "Advance Payment"),
    ("REMAINING", "Remaining Payment"),
)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = MongoFloatField()
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_status = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    paid = models.BooleanField(default=False)
    payment_type = models.CharField(
        max_length=20, choices=PAYMENT_TYPE_CHOICES, default="FULL"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class OrderPlaced(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    services = models.ForeignKey(Services, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PENDING")
    ordered_date = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, blank=True, null=True
    )
    is_advance_order = models.BooleanField(default=False)

    @property
    def total_cost(self):
        return self.quantity * self.services.discounted_price


class AdvanceBooking(models.Model):
    """Model for advance payment bookings (primarily for waterparks)"""

    BOOKING_STATUS_CHOICES = (
        ("AWAITING_PAYMENT", "Awaiting Payment"),
        ("PENDING", "Paid - Pending Verification"),
        ("VERIFIED", "Verified - Entry Allowed"),
        ("USED", "Already Used"),
        ("EXPIRED", "Booking Expired"),
        ("CANCELLED", "Cancelled"),
    )

    # Identifiers
    booking_code = models.CharField(max_length=6, unique=True, db_index=True)
    qr_code_data = models.TextField(blank=True)  # Base64 QR code image
    qr_hash = models.CharField(
        max_length=64, unique=True, blank=True, null=True
    )  # SHA-256 hash for validation

    # Relationships
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="advance_bookings"
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    service = models.ForeignKey(Services, on_delete=models.CASCADE)

    # Booking Details
    quantity = models.PositiveIntegerField(default=1)
    booking_date = models.DateField(help_text="Date for which the booking is made")
    total_amount = MongoFloatField()
    advance_paid = MongoFloatField()
    remaining_amount = MongoFloatField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(help_text="Booking expiration time")
    verified_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20, choices=BOOKING_STATUS_CHOICES, default="PENDING"
    )

    # Payment References
    advance_payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, related_name="advance_bookings"
    )
    final_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="final_bookings",
    )

    # Verification Tracking
    verified_by_staff = models.CharField(max_length=100, blank=True)
    verification_ip = models.GenericIPAddressField(null=True, blank=True)
    verification_attempts = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["booking_code"]),
            models.Index(fields=["status", "valid_until"]),
            models.Index(fields=["booking_date"]),
        ]

    def __str__(self):
        return f"{self.booking_code} - {self.customer.name} - {self.service.title}"

    def is_valid(self):
        """Check if booking is still valid"""
        from django.utils import timezone

        return self.status == "PENDING" and self.valid_until > timezone.now()
