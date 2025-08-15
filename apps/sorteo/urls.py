from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name='home'),
    path('sorteo/<int:sorteo_id>',views.details, name='detalle_sorteo'),
    path('sorteo/<int:sorteo_id>/pagar', views.create_payment, name='crear_pago'),
    path('payment/', views.payment_list, name='payment_list'),
    path('login/', views.login, name='login'), 
    path('payment/<int:payment_id>/verify', views.verify_payment, name='verify_payment'),
    path('find-my-tickets/', views.find_my_tickets, name='find_my_tickets'),
    path('sorteo/sorteo_list', views.sorteo_list, name='sorteo_list'),
    path('sorteo/create/', views.sorteo_edit, name='sorteo_create'),
    path('sorteo/<int:sorteo_id>/edit/', views.sorteo_edit, name='sorteo_edit'),
    path('logout/', views.logout_view, name='logout'),
    path('sorteo/<int:sorteo_id>/tickets', views.ticket_list, name='ticket_list'),
     path('sorteo/<int:sorteo_id>/check_availability/', views.check_availability, name='check_availability'),
    path('payment/zelle/create/', views.create_zelle_payment, name='create_zelle_payment'),
]   
