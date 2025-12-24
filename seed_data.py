
import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TSB.settings')
django.setup()

from TSBv1.models import Services, CATEGORY_CHOICES

dummy_images = [
    'service/resort1.jpg',
    'service/waterpark1.jpg',
    'service/villa1.jpg'
]

def seed_db():
    print("Clearing existing data...")
    Services.objects.all().delete()
    
    print("Seeding new data...")
    categories = [choice[0] for choice in CATEGORY_CHOICES]
    
    for i in range(10):
        category = random.choice(categories)
        service = Services.objects.create(
            title=f"Premium {category} {i+1}",
            selling_price=random.randint(5000, 20000),
            discounted_price=random.randint(2000, 4999),
            description=f"This is a wonderful {category} experience with amazing amenities.",
            composition="Pool, Wifi, Breakfast",
            servapp="Best Application",
            category=category
        )
        print(f"Created: {service.title}")
    
    print("Seeding complete!")

if __name__ == '__main__':
    seed_db()
