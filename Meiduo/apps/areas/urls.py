from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^areas/$', views.AreasView.as_view(), name='areas'),
    url(r'^address$', views.AddressView.as_view(), name='address'),
    url(r'^addresses/create/$', views.AddressCreateView.as_view(), name='create'),
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateAddressView.as_view(), name='update'),

]
