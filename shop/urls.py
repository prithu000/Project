from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_page, name='product'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order/<int:order_id>/success/', views.order_success, name='order_success'),
    path('order/<int:order_id>/track/', views.track_order, name='track_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='orders'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('google-auth/', views.google_auth_page, name='google_auth'),
    
    # Razorpay Payment API endpoints
    path('api/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('api/verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
]
