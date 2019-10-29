import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

# 从Redis购物车中查询出被勾选的商品信息进行结算并展示
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.response_code import RETCODE


class OrdersPlaceView(LoginRequiredMixin, View):
    """结算订单"""

    def get(self, request):
        """提供订单结算页面"""
        # 需求:展示用户的收货地址,支付方式(页面已写死),用户选择的订单信息
        # 隐含前提:只有登陆用户才能访问
        # 用户已加入购物车的数据已存储在redis中,数据结构: hash carts_user.id sku_id1 ,count1,sku_id2,count2
        # set: selected_user.id sku_id1,sku_id2,sku_id3

        # 获取数据
        user = request.user
        addresses = Address.objects.filter(user=user, is_deleted=False)
        redis_conn = get_redis_connection('carts')
        carts_data = redis_conn.hgetall('carts_%s' % user.id)
        selected_data = redis_conn.smembers('selected_%s' % user.id)
        # 数据处理 ---优化一步就可以
        selected_list = []
        for sku_id in selected_data:
            selected_list.append(int(sku_id))
        carts_dict = {}
        for sku_id, count in carts_data.items():
            if int(sku_id) in selected_list:
                carts_dict[int(sku_id)] = int(count)
        # 验证数据
        skus = []
        total_count = 0
        total_amount = 0
        for sku_id, count in carts_dict.items():
            try:
                sku = SKU.objects.get(id=sku_id)
            except SKU.DoesNotExist:
                return JsonResponse({'code': -1, 'erormsg': '商品信息不存在'})
            else:
                skus.append(sku)
                total_count += count
                amount = sku.price * count
                total_amount += amount
                sku.count = count
                sku.amount = amount

        # 返回响应
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': 10,
            'payment_amount': total_amount + 10
        }
        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredMixin, View):
    """提交订单"""

    def post(self, request):
        """保存订单信息和订单商品信息
        {address_id: this.nowsite,
        pay_method: this.pay_method}"""
        # ! 为保障一致性 需要使用事务 ,为应对并发(资源竞争)需使用队列或乐观锁...
        # 前端选择收货地址,支付方式,已勾选的商品,运费,优惠金额,进行提交
        # 后端
        # 获取数据: 收货地址,支付方式,商品信息,总金额,商品总数量,总支付金额
        data_dict = json.loads(request.body.decode())
        address_id = data_dict.get('address_id')
        pay_method = data_dict.get('pay_method')
        user = request.user
        # 验证数据:
        if not all([address_id, pay_method]):
            return HttpResponseBadRequest('缺少必传参数')
            # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception:
            return HttpResponseBadRequest('参数address_id错误')
            # 判断pay_method是否合法
        # OrderInfo.PAY_METHODS_ENUM['CASH']
        if pay_method not in ['1', OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return HttpResponseBadRequest('参数pay_method错误')
        import time
        time.sleep(8)
        # 生成订单id 当前日期时间+用户id
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S%f') + ('%09d' % user.id)
        # 订单数据准备
        address = Address.objects.get(id=address_id)
        # 总金额和总数量先设置成0,生成商品信息记录之前再进行更新
        total_count = 0
        total_amount = 0
        freight = 10
        # ORDER_STATUS_ENUM 是dict类型
        status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        # 库存充足的情况下生成订单记录,生成商品记录
        # 事务开始位置:针对With包裹的内容进行事务的跟踪
        with transaction.atomic():
            # 可以在事务中创建保存点来记录数据的特定状态，数据库出现错误时，可以回滚到数据保存点的状态。
            savepoint = transaction.savepoint()

            try:
                order_info = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=total_count,
                    total_amount=total_amount,
                    freight=freight,
                    pay_method=pay_method,
                    status=status
                )
                # 准备商品记录表数据 count price sku(sku_id) order(order_id)
                # 用户的商品记录保存在redis中:
                # hash carts_user.id sku_id1 ,count1,sku_id2,count2
                # set: selected_user.id sku_id1,sku_id2,sku_id3
                # 查询 redis 获取记录
                redis_conn = get_redis_connection('carts')
                # pl = redis_conn.pipeline()
                carts_data = redis_conn.hgetall('carts_%s' % user.id)
                selected_data = redis_conn.smembers('selected_%s' % user.id)
                # pl.execute()
                # 数据处理 取出已勾选的商品
                selected_dict = {}
                for id in selected_data:
                    selected_dict[int(id)] = int(carts_data[id])

                # carts_dict = {}
                # for sku_id, count in carts_data:
                #     if sku_id in selected_data:
                #         carts_dict[int(sku_id)] = int(count)
                # sku_ids = [sku_id for sku_id in carts_dict.keys()]
                # skus = SKU.objects.filter(id__in=sku_ids)

                # 获取数据
                # 乐观锁并不是真实存在的锁，而是在更新的时候判断此时的库存是否是之前查询出的库存(查询两次,两次结果一致则更新,否则回滚)
                # 如果相同，表示没人修改，可以更新库存
                # 否则表示别人抢过资源，不再执行库存更新

                for sku_id, count in selected_dict.items():
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        old_stock = sku.stock

                        if old_stock < count:
                            # 库存不足则回滚
                            transaction.savepoint_rollback(savepoint)
                            return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})

                        new_stock = sku.stock - count
                        new_sales = sku.sales + count
                        rect = SKU.objects.filter(id=sku_id, stock=old_stock).update(stock=new_stock, sales=new_sales)
                        if rect == 0:
                            continue

                        OrderGoods.objects.create(
                            order=order_info,
                            sku=sku,
                            count=count,
                            price=sku.price
                        )

                        #         2.6 累加计算,总数量和总金额
                        order_info.total_count += count
                        order_info.total_amount += (count * sku.price)
                        break
                    order_info.save()
            except Exception as e:
                # 有异常则回滚
                transaction.savepoint_rollback(savepoint)
                return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})

            else:
                # 无异常则提交事务
                transaction.savepoint_commit(savepoint)
                #     4.选中的数据应该删除
                # redis_conn.hdel('carts_%s'%user.id,*selected_ids)
                # redis_conn.srem('selected_%s'%user.id,*selected_ids)
                # 返回相应
                return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok',
                                     'order_id': order_info.order_id,
                                     'payment_amount': order_info.total_amount,
                                     'pay_method': order_info.pay_method})


class OrderSuccessView(LoginRequiredMixin, View):
    """提交订单成功"""

    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)
