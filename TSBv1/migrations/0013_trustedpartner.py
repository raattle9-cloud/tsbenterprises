# Generated manually for TrustedPartner model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TSBv1', '0012_auto_20260318_1346'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrustedPartner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('logo', models.ImageField(upload_to='partners/')),
                ('website_url', models.URLField(blank=True, default='')),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
