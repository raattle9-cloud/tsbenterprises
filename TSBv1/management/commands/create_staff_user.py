"""
Django management command to create staff1 test user
Usage: python manage.py create_staff_user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Creates staff1 test user with Staff group membership'

    def handle(self, *args, **kwargs):
        # Create or get Staff group
        staff_group, created = Group.objects.get_or_create(name='Staff')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Staff" group'))
        else:
            self.stdout.write('Staff group already exists')

        # Create or update staff1 user
        try:
            user = User.objects.get(username='staff1')
            # User exists, update password
            user.set_password('staff123')
            user.save()
            self.stdout.write(self.style.WARNING('Updated password for existing user "staff1"'))
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username='staff1',
                password='staff123',
                first_name='Staff',
                last_name='Member',
                email='staff1@tsbenterprises.com'
            )
            self.stdout.write(self.style.SUCCESS('Created user "staff1"'))

        # Add user to Staff group
        if not user.groups.filter(name='Staff').exists():
            user.groups.add(staff_group)
            self.stdout.write(self.style.SUCCESS('Added staff1 to Staff group'))
        else:
            self.stdout.write('staff1 already in Staff group')

        self.stdout.write(self.style.SUCCESS('\n✓ Staff user setup complete!'))
        self.stdout.write(self.style.SUCCESS('  Username: staff1'))
        self.stdout.write(self.style.SUCCESS('  Password: staff123'))
        self.stdout.write(self.style.SUCCESS('  Login at /accounts/login/ and you will be redirected to /staff/verify/'))
