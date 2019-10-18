import random

from django.http import HttpResponse, JsonResponse
from django.views import View
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from celery_tasks.sms import tasks
# from libs.yuntongxun.sms import CCP


class ImageCode(View):
    """返回图像验证码"""

    def get(self, request, uuid):
        '''
        :param request 请求对象
        :param uuid  唯一标识图形验证码所属于的用户
        :return image/jpeg
        '''
        # 01 生成图片验证码
        text, image = captcha.generate_captcha()

        # 02 保存验证码(uuid:text)
        # message_code是要连接的redis配置的别名
        redis_conn = get_redis_connection('message_code')
        # setex(key,expire_time,value
        redis_conn.setex('img_%s' % uuid, 120, text)
        # 返回图片二进制格式的数据 告诉浏览器解析图片格式数据,浏览器才能正常加载显示图片
        return HttpResponse(image, content_type='image/jpeg')


class SmsCode(View):
    """发送短信功能"""

    def get(self, request, mobile):
        '''
        :param request:
        :param mobile: 手机号
        :return: json sms_code
        '''
        image_code = request.GET.get('image_code')
        image_code_id = request.GET.get('image_code_id')
        # 获取send_flag
        redis_conn = get_redis_connection('message_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 检查短信发送状态
        if send_flag:
            return JsonResponse({'code': 4001, 'errmsg': '发送短信过于频繁'})

        image_code_server = redis_conn.get('img_%s' % image_code_id)

        if image_code_server is None:
            return JsonResponse({'code': '4002', 'errmsg': '图片验证码已失效'})

        image_code_server = image_code_server.decode()
        if image_code.lower() != image_code_server.lower():
            return JsonResponse({'code': '-2', 'errmsg': '图片验证码无效'})
        sms_code = '%06d' % random.randint(0, 999999)
        tasks.send_sms_code.delay(mobile, sms_code)
        return JsonResponse({'msg': 'ok', 'code': '0'})
