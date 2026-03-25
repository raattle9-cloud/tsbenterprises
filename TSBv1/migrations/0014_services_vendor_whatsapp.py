# Generated manually for vendor_whatsapp field on Services model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TSBv1', '0013_trustedpartner'),
    ]

    operations = [
        migrations.AddField(
            model_name='services',
            name='vendor_whatsapp',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Vendor WhatsApp number in international format (digits only, e.g. 919876543210)',
                max_length=15,
            ),
        ),
    ]
