from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^oauth_callback$', views.QQLoginView.as_view(), name='oauth_callback'),
]