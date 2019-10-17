from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCode.as_view(), name='image_codes'),
    url(r'^sms_codes/(?P<mobile>1[3456789]\d{9})/', views.SmsCode.as_view(), name='sms_codes'),
]
