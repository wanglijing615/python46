from django.contrib.auth import login
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django_redis import get_redis_connection
from django.views import View
from apps.users.models import UserModel
from utils.users import UsernameMobile

'''
get 返回注册页面
post
    1 获取用户数据
    2 验证数据
        必填项不能为空

        用户名符合规则
        用户名不能重复

        密码符合规则
        确认密码和密码输入一致

        手机号符合规则
        手机号不能重复
    3 保存数据
    4 返回结果
'''


# 用户注册页
class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 获取用户数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        image_code_client = request.POST.get('pic_code')
        sms_code_client = request.POST.get('sms_code')
        # image_code_id=request.POST.get('image_code_id')

        # 验证数据
        # 必填项
        if not all([username, password, password2, mobile, image_code_client, sms_code_client]):
            return HttpResponseBadRequest('必填项不能为空')
        import re
        # 用户名规则
        if not re.match(r'[a-zA-Z0-9]{6,20}', username):
            return HttpResponseBadRequest('请输入6-20个字符的用户名')
        # # 判断用户名是否重复
        # count =UserModel.objects.filter('username=username').count()
        # if count==1:
        #     return HttpResponseBadRequest('用户名已存在')
        # 密码规则验证
        if not re.match(r'[a-zA-Z0-9]{8,20}', password):
            return HttpResponseBadRequest('请输入8-20位的密码')
        if password2 != password:
            return HttpResponseBadRequest('两次密码输入不一致')
        # 手机号规则
        if not re.match(r'1[345789]\d{9}', mobile):
            return HttpResponseBadRequest('请输入正确的手机号码')
        # # 判断图片验证码的有效性
        redis_conn = get_redis_connection('message_code')
        # image_code_serveer = redis_conn.get('img_%s' % image_code_id)
        # if image_code_serveer == None:
        #     return render(request, 'register.html', {'image_code_errmsg': '验证码已失效'})
        #
        # image_code_server = image_code_serveer.decode()
        # if image_code_client.lower() != image_code_server.lower():
        #     return render(request, 'register.html', {'image_code_errmsg': '验证码错误'})
        # 判断短信验证码的有效性
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        sms_code_server = sms_code_server.decode()
        if sms_code_client.lower() != sms_code_server.lower:
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})

        # 判断是否勾选协议
        if not allow:
            return HttpResponseBadRequest('请阅读并同意协议')

        # 保存注册数据
        try:
            user = UserModel.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            print(e)
            return JsonResponse({'msg': 'connect db error'})
        # return JsonResponse({'msg': 'success'})
        # 添加session
        # request.session['username'] = username
        # user = UserModel.objects
        # user为创建表记录的user对象
        login(request, user)
        return render(request, 'index.html')


# 用户名是否重复检查
class UsernameCountView(View):
    def get(self, request, username):
        # 数据库中查询username count
        try:
            count = UserModel.objects.filter(username=username).count()
        except Exception as e:
            print(e)
            return JsonResponse({'count': -1})
        return JsonResponse({'count': count, 'msg': '用户名重复'})


# 手机号是否重复检查
class MobileCountView(View):
    def get(self, request, mobile):
        try:
            count = UserModel.objects.filter(mobile=mobile).count()
        except Exception as e:
            print(e)
            return JsonResponse({'count': -1})
        return JsonResponse({'count': count, 'msg': '手机号重复'})


class LoginView(View):
    """用户登陆"""

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        '''
        :param request: 请求对象
        :return: 登陆成功页
        '''
        # 获取数据进行验证
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remembered=request.POST.get('remembered')

        # 判断必填项
        if not all([username, password]):
            return JsonResponse({'code': -2, 'errormsg':'必填项为空'})
        # 判断用户信息和数据库中是否一致----认证用户
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)

        if user is None:
            return render(request, 'login.html', {'errormsg':'用户名或密码错误'})
        # 状态保存--会话有效期为关闭浏览器
        login(request,user)
        # 记住登陆 ---设置会话有效期更长
        if remembered == 'on':
            # None 默认有效期2周
            request.session.set_expiry(None)
        # 结果响应
        response = redirect(reverse('contents:index'))
        # 设置cookie 给浏览器渲染登陆页时取数据
        response.set_cookie('username', user.username, max_age=1)
        return response

class LogoutView(View):
    """退出登陆"""
    def get(self, request):
        # 退出登陆关键： 清除session 通过调用logout(), 清除cookie,重定向回登陆页
        # # 清除session
        # request.session.flush()
        from  django.contrib.auth import logout
        logout(request)
        # 删除cookie 或设置成有效期为0
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', None, max_age=0)
        return  redirect(reverse('users:login'))


from django.contrib.auth.mixins import LoginRequiredMixin

class UserCenterView(LoginRequiredMixin,View):
    """用户中心"""
    def get(self, request):
        # 判断只有登陆用户才能进入个人中心
        # if request.user.is_authenticated:
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect(reverse('users:login'))

        return render(request, 'user_center_info.html')
