from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Create your models here.

CATEGORY_CHOICES = (
    ('RE', 'Resort'),
    ('WP', 'Waterpark'),
    ('DP', 'Destination_packages'),
    ('DB', 'Dhaba'),
    ('VI', 'Villas'),
    ('GO', 'Game_On'),

)
STATE_CHOICES = (
    ("AN","Andaman and Nicobar Islands"),
   ("AP","Andhra Pradesh"),
   ("AR","Arunachal Pradesh"),
   ("AS","Assam"),
   ("BR","Bihar"),
   ("CG","Chhattisgarh"),
   ("CH","Chandigarh"),
   ("DN","Dadra and Nagar Haveli"),
   ("DD","Daman and Diu"),
   ("DL","Delhi"),
   ("GA","Goa"),
   ("GJ","Gujarat"),
   ("HR","Haryana"),
   ("HP","Himachal Pradesh"),
   ("JK","Jammu and Kashmir"),
   ("JH","Jharkhand"),
   ("KA","Karnataka"),
   ("KL","Kerala"),
   ("LA","Ladakh"),
   ("LD","Lakshadweep"),
   ("MP","Madhya Pradesh"),
   ("MH","Maharashtra"),
   ("MN","Manipur"),
   ("ML","Meghalaya"),
   ("MZ","Mizoram"),
   ("NL","Nagaland"),
   ("OD","Odisha"),
   ("PB","Punjab"),
   ("PY","Pondicherry"),
   ("RJ","Rajasthan"),
   ("SK","Sikkim"),
   ("TN","Tamil Nadu"),
   ("TS","Telangana"),
   ("TR","Tripura"),
   ("UP","Uttar Pradesh"),
   ("UK","Uttarakhand"),
   ("WB","West Bengal")
)

class Services(models.Model):
    title = models.CharField(max_length=100)
    selling_price = models.FloatField()
    discounted_price = models.FloatField()
    description = models.TextField()
    composition = models.TextField(default='')
    servapp = models.TextField(default='')
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)

    def __str__(self):
        return self.title

    def get_primary_image(self):
        return self.images.first()

    def get_primary_image_url(self):
        image = self.get_primary_image()
        if image and image.image:
            return image.image.url
        return ''


class ServiceImage(models.Model):
    service = models.ForeignKey(
        Services,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='service/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

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
            return ''
        
        image_path = str(self.image)
        
        # If it's already a full URL (Cloudinary), return it
        if image_path.startswith('http'):
            return image_path
        
        # Check if the image exists on Cloudinary by checking if the URL is a Cloudinary URL
        try:
            url = self.image.url
            if 'cloudinary.com' in url:
                return url
        except Exception:
            pass
        
        # Fallback to local static URL for existing local images
        # Images are stored in static/images/service/
        from django.conf import settings
        return f"{settings.STATIC_URL}images/{image_path}"
    
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=20)
    mobile = models.CharField(max_length=10, validators=[
        RegexValidator(
            regex=r'^\d{10}$',
            message='Mobile number must be 10 digits',
            code='invalid_mobile'
        ),
    ])
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
        unique_together = ('user', 'services')

    def __str__(self):
        return f"{self.user.username} - {self.services.title}"


#Payment models
STATUS_CHOICES =(
    ('SUCCESS', 'SUCCESS'),
    ('PENDING', 'PENDING'),
    ('FAILED', 'FAILED'),
)
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_status = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    paid = models.BooleanField(default=False)

class OrderPlaced(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    services = models.ForeignKey(Services, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    ordered_date = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, blank=True, null=True)

    @property
    def total_cost(self):
        return self.quantity * self.services.discounted_price
    
