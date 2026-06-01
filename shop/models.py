"""
Models for CamCap Shop — Product, Order, and UserProfile.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Product(models.Model):
    """Single product model for CamCap."""
    name = models.CharField(max_length=200, default='CamCap')
    tagline = models.CharField(max_length=300, default='Capture. Vlog. Share.')
    description = models.TextField(default='CamCap is more than just a cap. It\'s your point of view, your creative edge, your everyday companion.')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=2999.00)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=4999.00)
    in_stock = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0


ORDER_STATUS = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]


class Order(models.Model):
    """Customer order for CamCap."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping details
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Order status
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, default='cod')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} — {self.user.username} — {self.status}'

    @property
    def order_id(self):
        return f'CC{self.id:06d}'
