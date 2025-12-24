"""
Management command to migrate local service images to Cloudinary.
This uploads all existing local images to Cloudinary and updates the database.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
import cloudinary
import cloudinary.uploader
from TSBv1.models import ServiceImage


class Command(BaseCommand):
    help = 'Migrate local service images to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            api_key=settings.CLOUDINARY_STORAGE.get('API_KEY'),
            api_secret=settings.CLOUDINARY_STORAGE.get('API_SECRET'),
        )
        
        self.stdout.write(self.style.NOTICE('Starting image migration to Cloudinary...'))
        
        local_media_root = os.path.join(settings.BASE_DIR, 'static', 'images')
        
        service_images = ServiceImage.objects.all()
        migrated = 0
        skipped = 0
        failed = 0
        
        for img in service_images:
            image_path = str(img.image)
            
            # Check if already a Cloudinary URL
            if image_path.startswith('http') or 'cloudinary' in image_path:
                self.stdout.write(f'  [SKIP] {image_path} - already on Cloudinary')
                skipped += 1
                continue
            
            # Build local file path - handle different path formats
            # Could be 'service/file.jpg' or 'media/service/file.jpg'
            if image_path.startswith('media/'):
                # Strip 'media/' prefix since MEDIA_ROOT already points to static/images
                clean_path = image_path[6:]  # Remove 'media/'
            else:
                clean_path = image_path
            
            local_path = os.path.join(local_media_root, clean_path)
            
            if not os.path.exists(local_path):
                self.stdout.write(self.style.WARNING(f'  [MISSING] {local_path} - file not found'))
                failed += 1
                continue
            
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] Would upload: {local_path}')
                migrated += 1
                continue
            
            try:
                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    local_path,
                    folder='service',
                    resource_type='image',
                )
                
                # Update the database record to point to Cloudinary URL
                # Get the public_id which will be used by cloudinary_storage
                public_id = result.get('public_id')
                
                # The cloudinary_storage backend expects just the path after upload
                # Format: folder/filename (without extension)
                new_path = public_id
                
                img.image = new_path
                img.save()
                
                self.stdout.write(self.style.SUCCESS(f'  [OK] {image_path} -> {new_path}'))
                migrated += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [FAILED] {image_path}: {str(e)}'))
                failed += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Migration complete!'))
        self.stdout.write(f'  Migrated: {migrated}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Failed: {failed}')
