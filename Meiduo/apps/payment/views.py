import os

from alipay import AliPay
from django.contrib.auth.mixins import LoginRequiredMixin

# 测试账号：axirmj7487@sandbox.com
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from Meiduo import settings
from apps.orders.models import OrderInfo
from apps.payment.models import Payment
from utils.response_code import RETCODE


class PaymentView(LoginRequiredMixin, View):
    """订单支付功能"""

    def get(self, request, order_id):
        '''
         生成用户跳转的支付宝链接
         导入支付宝 python sdk 按照sdk开发:
         设置项目的公钥(保存到支付宝)私钥(自己项目里加密数据使用) 及支付宝的公钥(保存到项目里验证数据使用) 私钥(支付宝自己加密数据使用)
         1.接收要支付的订单号参数 并验证订单是否存在
         2.调用class AliPay()创建支付对象
         3.调用alipay.api_alipay_trade_page_pay()方法生成order_string(包括订单号 支付金额 主题 支付回调地址)
         4.拼接地址:沙箱网关+ order_string
         5.返回响应
        '''
        # 查询要支付的订单
        user = request.user
        try:
            # 保证接收的订单号的有效性
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return HttpResponseBadRequest('订单信息错误')

        # 读取私钥和公钥
        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()

        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            # app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            # alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 电脑网站支付，需要跳转到https: // openapi.alipay.com / gateway.do? + order_string
        # 生成登录支付宝连接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            # 注意金额传参时需转换成str
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})

class PaymentStatusView(View):
    """支付结果视图+保存支付结果"""

    def get(self, request):
        '''
        1.支付回调时请求(GET方法) 会回传no_trade out_no_trade等参数
        2.为保障安全性 需进行验签(确认请求是支付宝发送过来的):用支付宝的公钥对签名进行验证
        3.验证通过则保存 并返回成功页面
        :param request:
        :return: 支付成功页
        '''
        # 读取私钥和公钥
        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        # 创建支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 0.需要先验证交易成功
        # for django users
        data = request.GET.dict()

        # 拿出签名数据
        signature = data.pop("sign")

        # 验证签名 (验证签名类型)
        success = alipay.verify(data, signature)
        if success:
            # 1.获取 支付宝交易流水号, 获取商家订单id,把这2个信息,保存起来
            trade_no = data.get('trade_no')
            out_trade_no = data.get('out_trade_no')

            Payment.objects.create(
                order_id=out_trade_no,
                trade_id=trade_no
            )

            # 修改订单的状态
            OrderInfo.objects.filter(order_id=out_trade_no).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

            return render(request, 'pay_success.html', context={'trade_no': trade_no})
        else:
            return render(request, '404.html', context="支付异常")

