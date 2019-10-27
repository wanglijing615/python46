"""Meiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

# 测试log输出
from django.http import HttpResponse
import logging


def test(request):
    loger = logging.getLogger('django')
    loger.debug('debug info')
    loger.info('log info')
    loger.error('log error')
    return HttpResponse('test')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(r'^test', test)
    url(r'', include('apps.users.urls', namespace='users')),
    url(r'', include('apps.contents.urls', namespace='contents')),
    url(r'', include('apps.verifications.urls', namespace='verifications')),
    url(r'', include('apps.oauth.urls', namespace='oauth')),
    url(r'', include('apps.areas.urls', namespace='areas')),
    url(r'', include('apps.goods.urls', namespace='goods')),
    url(r'', include('apps.carts.urls', namespace='carts')),



]
