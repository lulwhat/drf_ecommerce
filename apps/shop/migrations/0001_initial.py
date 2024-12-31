# Generated by Django 5.1.4 on 2024-12-19 08:03

import autoslug.fields
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sellers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name', unique=True)),
                ('image', models.ImageField(upload_to='category_images/')),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='name', unique=True)),
                ('desc', models.TextField()),
                ('price_old', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('price_current', models.DecimalField(decimal_places=2, max_digits=10)),
                ('in_stock', models.IntegerField(default=5)),
                ('image1', models.ImageField(upload_to='product_images/')),
                ('image2', models.ImageField(blank=True, upload_to='product_images/')),
                ('image3', models.ImageField(blank=True, upload_to='product_images/')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='shop.category')),
                ('seller', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='sellers.seller')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
