"""
Views for CamCap Shop — Product, Cart, Checkout, Orders, Auth.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Product, Order


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
        payment_method='cod',
    )
    
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


def signup_view(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        errors = []
        if not username:
            errors.append('Username is required.')
        if not password:
            errors.append('Password is required.')
        if password != password2:
            errors.append('Passwords do not match.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'shop/signup.html', {
                'username': username, 'email': email
            })
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, f'Welcome to CamCap, {username}!')
        
        # Redirect to next URL if provided
        next_url = request.GET.get('next', '/')
        return redirect(next_url)
    
    return render(request, 'shop/signup.html')


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'shop/login.html')


def logout_view(request):
    """Logout the user."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')
