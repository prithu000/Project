"""
Views for CamCap Shop — E-Commerce with Google OAuth & Razorpay
"""
import json
import hmac
import hashlib
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Product, Order
from .email_utils import send_order_confirmation_to_admin, send_order_confirmation_to_customer

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def product_page(request):
    """Display the CamCap product page."""
    product = Product.objects.first()
    if not product:
        # Create default product if none exists
        product = Product.objects.create(
            name='CamCap',
            tagline='Capture. Vlog. Share.',
            description='CamCap is more than just a cap. It\'s your point of view, your creative edge, your everyday companion. Perfect for vlogging, travel, and hands-free recording.',
            price=2999.00,
            original_price=4999.00,
            in_stock=True,
            features=[
                'POV Ready — Built-in camera mount',
                'Lightweight & Comfortable — All-day wear',
                'Durable — Premium quality fabric',
                'SD Card Recording — Up to 128GB',
                'Hands-Free Convenience',
                'Perfect for Travel & Vlogging',
            ]
        )
    return render(request, 'shop/product.html', {'product': product})


@login_required
def checkout_page(request):
    """Checkout page with shipping form."""
    product = Product.objects.first()
    if not product:
        return redirect('shop:product')
    
    quantity = int(request.GET.get('qty', 1))
    total = product.price * quantity
    
    return render(request, 'shop/checkout.html', {
        'product': product,
        'quantity': quantity,
        'total': total,
    })


@login_required
@require_POST
def place_order(request):
    """Process the order form submission."""
    product = Product.objects.first()
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('shop:product')
    
    quantity = int(request.POST.get('quantity', 1))
    total = product.price * quantity
    payment_method = request.POST.get('payment', 'cod')
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        product=product,
        quantity=quantity,
        total_price=total,
        full_name=request.POST.get('full_name', ''),
        phone=request.POST.get('phone', ''),
        email=request.POST.get('email', ''),
        address=request.POST.get('address', ''),
        city=request.POST.get('city', ''),
        state=request.POST.get('state', ''),
        pincode=request.POST.get('pincode', ''),
        payment_method=payment_method,
    )
    
    # Handle Razorpay payment details
    if payment_method == 'online':
        order.razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        order.razorpay_order_id = request.POST.get('razorpay_order_id', '')
        order.razorpay_signature = request.POST.get('razorpay_signature', '')
        order.payment_status = 'completed'
        order.save()
    
    # Send email notifications
    try:
        send_order_confirmation_to_admin(order)
        send_order_confirmation_to_customer(order)
    except Exception as e:
        print(f"Email Error: {e}")
    
    messages.success(request, f'Order placed successfully! Your order ID is {order.order_id}')
    return redirect('shop:order_success', order_id=order.id)


@login_required
def order_success(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {'order': order})


@login_required
def order_history(request):
    """Display user's order history."""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """Display detailed order tracking page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})


@login_required
def track_order(request, order_id):
    """Track specific order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return JsonResponse({
        'order_id': order.order_id,
        'status': order.status,
        'status_display': order.get_status_display(),
        'created_at': order.created_at.strftime('%B %d, %Y at %I:%M %p'),
        'updated_at': order.updated_at.strftime('%B %d, %Y at %I:%M %p'),
    })


def login_view(request):
    """Login page with Google OAuth button"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'shop/login.html')


def signup_view(request):
    """Signup page with Google OAuth button"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'shop/signup.html')


def google_auth_page(request):
    """Interactive Google Auth page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'shop/google_auth.html')


def logout_view(request):
    """Logout the user."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')


# ========== RAZORPAY PAYMENT INTEGRATION ==========

@login_required
@require_POST
def create_razorpay_order(request):
    """Create Razorpay order for payment processing."""
    try:
        data = json.loads(request.body)
        amount = int(data.get('amount', 0))  # Amount in paise
        
        # Validate minimum amount
        if amount < 100:
            return JsonResponse({
                'success': False,
                'message': 'Amount must be at least ₹1'
            }, status=400)
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'receipt': f'order_rcpt_{request.user.id}_{amount}',
            'payment_capture': 1  # Auto capture
        })
        
        return JsonResponse({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'key_id': settings.RAZORPAY_KEY_ID
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid JSON: {str(e)}'
        }, status=400)
    except Exception as e:
        # Log the full error
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def verify_razorpay_payment(request):
    """Verify Razorpay payment signature."""
    try:
        data = json.loads(request.body)
        
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Validate required fields
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required payment details'
            }, status=400)
        
        # Verify signature
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return JsonResponse({
                'success': False,
                'message': 'Payment signature verification failed'
            }, status=400)
        
        # Signature verified - Payment successful
        return JsonResponse({
            'success': True,
            'message': 'Payment verified successfully',
            'payment_id': razorpay_payment_id,
            'order_id': razorpay_order_id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
