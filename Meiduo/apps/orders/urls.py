from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^orders/place$', views.OrdersPlaceView.as_view(), name='place_orders'),

]
