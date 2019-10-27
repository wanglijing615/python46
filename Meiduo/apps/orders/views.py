from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

# 从Redis购物车中查询出被勾选的商品信息进行结算并展示
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import Address


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
        addresses = Address.objects.filter(user=user,is_deleted=False)
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
