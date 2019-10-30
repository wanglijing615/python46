from django.conf.urls import url
from django.views import View

from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^username/(?P<username>[a-zA-Z0-9_-]{5,20})/$', views.UsernameCountView.as_view(), name='username'),
    url(r'^mobile/(?P<mobile>1[3456789]\d{9})/$', views.MobileCountView.as_view(), name='mobile'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^center/$', views.UserCenterView.as_view(), name='center'),
    url(r'^emails/$', views.EmailView.as_view(), name='emails'),
    url(r'^emailactive/$', views.EmailActive.as_view(), name='emailactive'),
    url(r'^findpassword/$', views.FindPasswordView.as_view(), name='findpassword'),

]
