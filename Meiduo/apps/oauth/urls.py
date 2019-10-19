from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^oauth2.0/authorize/$', views.QQAuthURLView.as_view()),
]
