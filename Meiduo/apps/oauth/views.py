import json
import re

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import secret_openid, check_openid
from apps.users.models import UserModel

'''
QQ_CLIENT_ID = '101518219'

QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'

QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'
'''

from QQLoginTool.QQtool import OAuthQQ


class QQLoginView(View):
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return HttpResponseBadRequest('没有code')
        else:
            # 获取token ---QQ登陆后才会返回token
            # 1 拼装请求参数
            oauth = OAuthQQ(client_id=101518219, client_secret='418d84ebdc7241efb79536886ae95224',
                            redirect_uri='http://www.meiduo.site:8000/oauth_callback', state=next)
            # 2调用登陆接口
            oauth.get_qq_url()
            # 3 获取token
            token = oauth.get_access_token(code)
            # 4 获取openid
            open_id = oauth.get_open_id(token)
            #

            # open_id= secret_openid(open_id)

            # 判断用户是应该直接进入首页还是需要绑定账号
            from apps.oauth.models import OAuthQQUser
            try:
                qq_user = OAuthQQUser.objects.get(openid=open_id)
            except OAuthQQUser.DoesNotExist:
                return render(request, 'oauth_callback.html', context=({'openid': open_id}))
            else:
                login(request, qq_user)
                # 设置cookie
                response = redirect(reverse('contents:index'))
                response.set_cookie('username', qq_user.user.username, max_age=24 * 3600)
                return response

    def post(self, request):

        username = request.POST.get('mobile')
        pwd = request.POST.get('pwd')
        # sms_code = request.POST.get('sms_code')
        secret_openid = request.POST.get('openid')
        #解密.
        openid= check_openid(secret_openid)
        # 验证数据
        try:
            user = UserModel.objects.get(mobile=username)
        except UserModel.DoesNotExist:
            user = UserModel.objects.create_user(username=username, password=pwd, mobile=username)
        else:
            if not user.check_password(pwd):
                return HttpResponseBadRequest('密码错误')
        # 绑定用户和openid
        OAuthQQUser.objects.create(user=user, openid=openid)
        # 登陆
        login(request, user)
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, expires=None)
        return response
