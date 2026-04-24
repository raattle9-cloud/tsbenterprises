import uuid
import django.db.models.deletion
import TSBv1.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TSBv1', '0014_services_vendor_whatsapp'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_no', models.CharField(max_length=50, unique=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('amount', TSBv1.models.MongoFloatField()),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='invoices',
                    to='TSBv1.orderplaced',
                )),
                ('advance_booking', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='invoices',
                    to='TSBv1.advancebooking',
                )),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='TSBv1.customer',
                )),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='TSBv1.services',
                )),
                ('payment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='TSBv1.payment',
                )),
            ],
        ),
    ]
