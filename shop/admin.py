from django.contrib import admin
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'original_price', 'in_stock', 'created_at')
    list_filter = ('in_stock',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'full_name', 'phone', 'city', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'phone', 'email', 'city')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)
