"""
Email utilities for sending order notifications.
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_order_confirmation_to_admin(order):
    """Send order details to admin email."""
    subject = f'New Order Received - {order.order_id}'
    message = f"""
New Order Details:
==================
Order ID: {order.order_id}
Customer: {order.full_name}
Email: {order.email}
Phone: {order.phone}
Product: {order.product.name}
Quantity: {order.quantity}
Total: ₹{order.total_price}

Shipping Address:
{order.address}
{order.city}, {order.state} - {order.pincode}

Payment: {order.payment_method.upper()}
Status: {order.get_status_display()}

Order placed on: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error sending admin email: {e}')
        return False


def send_order_confirmation_to_customer(order):
    """Send order confirmation to customer email."""
    subject = f'Order Confirmation - {order.order_id} | CamCap'
    message = f"""
Dear {order.full_name},

Thank you for your order! We're excited to get your CamCap to you.

Order Details:
==============
Order ID: {order.order_id}
Product: {order.product.name}
Quantity: {order.quantity}
Total: ₹{order.total_price}

Shipping Address:
{order.address}
{order.city}, {order.state} - {order.pincode}

Payment Method: {order.payment_method.upper()}

What's Next?
============
1. We'll process your order within 24-48 hours
2. You'll receive a shipping notification with tracking details
3. Estimated delivery: 5-7 business days

Track Your Order:
Visit https://camcap.com/shop/orders/ to track your order status.

Need Help?
Contact us at {settings.ADMIN_EMAIL}

Thank you for choosing CamCap!

Best regards,
The CamCap Team
"""
    
    if not order.email:
        return False
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error sending customer email: {e}')
        return False
