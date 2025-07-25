from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name='home'),
    path('sorteo/<int:sorteo_id>',views.details, name='detalle_sorteo'),
    path('sorteo/<int:sorteo_id>/pagar', views.create_payment, name='crear_pago'),
    path('payment/', views.payment_list, name='payment_list'),
    path('login', views.login, name='login'), 
    path('payment/<int:payment_id>/verify', views.verify_payment, name='verify_payment'),
    path('find-my-tickets/', views.find_my_tickets, name='find_my_tickets'),
]   
