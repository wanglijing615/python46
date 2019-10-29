from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^orders/place/$', views.OrdersPlaceView.as_view(), name='place_orders'),
    url(r'^orders/commit/$', views.OrderCommitView.as_view(), name='orders_commit'),
    url(r'^orders/success/$', views.OrderSuccessView.as_view(), name='orders_success'),

]
