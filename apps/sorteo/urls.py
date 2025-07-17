from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name='home'),
    path('sorteo/<int:sorteo_id>',views.details, name='detalle_sorteo'),
    path('sorteo/<int:sorteo_id>/pagar', views.create_payment, name='crear_pago')
]   
