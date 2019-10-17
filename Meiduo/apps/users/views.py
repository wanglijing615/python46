from django.contrib.auth import login
from django.http import HttpResponse
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django_redis import get_redis_connection
# Create your views here.
from django.views import View
from apps.users.models import UserModel


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
        image_code_client =request.POST.get('image_code')
        sms_code_client =request.POST.get('sms_code')
        # image_code_id=request.POST.get('image_code_id')

        # 验证数据
        # 必填项
        if not all([username, password, password2, mobile,image_code_client,sms_code_client]):
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
        sms_code_server =redis_conn.get('sms_%s' % mobile)
        sms_code_server=sms_code_server.decode()
        if sms_code_client.lower()!=sms_code_server.lower:
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