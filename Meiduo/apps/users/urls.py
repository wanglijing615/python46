from django.conf.urls import url
from . import views

urlpatterns =[
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^username/(?P<username>[a-zA-Z0-9_-]{5,20})/$', views.UsernameCountView.as_view(), name='username'),
    url(r'^mobile/(?P<mobile>1[3456789]\d{9})/$', views.MobileCountView.as_view(), name='mobile'),

]