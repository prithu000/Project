from django.contrib import admin
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'original_price', 'discount_percent', 'in_stock', 'created_at')
    list_editable = ('price', 'original_price', 'in_stock')
    list_filter = ('in_stock', 'created_at')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'tagline', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price'),
            'description': 'Update product price here. Changes are reflected immediately.'
        }),
        ('Availability', {
            'fields': ('in_stock',)
        }),
        ('Features', {
            'fields': ('features',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'full_name', 'phone', 'status', 'payment_status', 'total_price', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'phone', 'email', 'city', 'user__username')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'status_updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'product', 'quantity', 'total_price')
        }),
        ('Customer Details', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Order Status & Tracking', {
            'fields': ('status', 'tracking_number', 'courier_name', 'estimated_delivery', 'status_updated_at'),
            'description': '🚚 Update tracking information here. Customer will see these updates on their order page.'
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'razorpay_order_id', 'razorpay_payment_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_id(self, obj):
        return obj.order_id
    order_id.short_description = 'Order ID'
