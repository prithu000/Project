from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_page, name='product'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order/<int:order_id>/success/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='orders'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]
