import base64
import json
import pickle

from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
# {sku_id: 2, count: 1}
from django_redis import get_redis_connection

from apps.goods.models import SKU
from utils.response_code import RETCODE


class CartsView(View):
    """购物车管理"""

    def post(self, request):
        '''
        添加商品到购物车
        :param request: {sku_id: 2, count: 1}
        :return: json data
        '''
        # 获取参数数据
        user = request.user
        sku_id = json.loads(request.body.decode()).get('sku_id')
        count = json.loads(request.body.decode()).get('count')
        selected = json.loads(request.body.decode()).get('selected', True)
        if not all([]):
            return HttpResponseBadRequest('缺少必传参数')
        # 判断用户是否为登陆用户
        # 登陆用户　购物车数据保存到redis
        if user.is_authenticated:
            # 判断商品是否存在
            try:
                SKU.objects.get(id=sku_id)
            except SKU.DoesNotExist:
                return HttpResponseBadRequest('商品不存在')
            # 判断count是否为数字
            try:
                count = int(count)
            except Exception:
                return HttpResponseBadRequest('参数count有误')
            # selected可能传可能不传　判断是否为boolen
            if selected:
                if not isinstance(selected, bool):
                    return HttpResponseBadRequest('参数selected有误')

            # 如存在则组装数据hash{sku_id:{count:1},sku_id:{count:2}}　(sku_id,sku_id)连接redis进行保存
            # 数据结构: hash,hmset key,feild1,value1,feild2,value2; sadd key value1 value2
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 新增购物车数据 hincrby 增量式的添加数据，同样的feild　数值进行累加
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            pl.execute()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        # 非登陆用户购物车数据保存到cookie
        else:
            # cookie里数据结构:key:value {sku_id:{count:1,selected:True},sku_id:{count:2,selected:False}}
            # cookie里数据需加密，这里使用base64
            # 判断cookie里是否有购物车数据，如有需取出进行累加，没有则直接创建　设置
            carts_str = request.COOKIES.get('carts')
            if not carts_str:
                cookie_data = {
                    sku_id: {'count': count, 'selected': True}}
            else:
                # 解析数据
                carts_byte = base64.b64encode(carts_str)
                cookie_data = pickle.loads(carts_byte)
                # 如果sku_id在　cookie dict中则进行累加修改，如果不在则新增
                if sku_id in cookie_data:
                    cookie_count = cookie_data['sku_id']['count']
                    count += cookie_count
                    cookie_data[sku_id] = {
                        'count': count,
                        'selected': selected
                    }
            # 对数据进行二进制转换　进行base64
            new_carts_byte = pickle.dumps(cookie_data)
            new_carts_data = base64.b64encode(new_carts_byte)
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
            response.set_cookie('carts', new_carts_data, max_age=7 * 24 * 3600)
            return response

    def get(self, request):
        ''' 获取购物车数据'''
        # 登陆用户从redis取,如果cookie有数据还需合并到redis,否则直接从cookie取数据
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            # hgetall查询所有的字段及值　组装成列表，不存在返回空列表，而hget查询指定的指定对应的值
            carts_data = redis_conn.hgetall('carts_%s' % user.id)
            selected_data = redis_conn.smembers('selected_%s' % user.id)
            # 查询商品信息　组装返回数据
            # 将redis中的数据构造成跟cookie中的格式一致，方便统一查询
            cart_dict = {}
            for sku_id, count in carts_data.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_data
                }
        else:
            carts_data = request.COOKIES.get('carts')
            if carts_data is not None:
                # 解密
                carts_data = base64.b64decode(carts_data)
                # 二进制转python dict
                cart_dict = pickle.loads(carts_data)
                # {sku_id:{count:1},sku_id:{count:2}}
            else:
                cart_dict = {}

        ids = cart_dict.keys()  # [1,2,3,4,5,6] 取出所有的sku_id

        # 5 根据商品id进行商品信息的查询
        carts_list = []
        for id in ids:
            sku = SKU.objects.get(id=id)
            # 6 将对象转换为字典
            carts_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * cart_dict.get(sku.id).get('count')),

            })
        context = {
            'cart_skus': carts_list,
        }
        return render(request, 'cart.html', context)

    def put(self, request):
        '''
        修改购物车数据：商品数量，选中状态
        注意点：无论是redis还是cookie数据，直接更新数据（直接创建数据）即可
        :param request:
        :return:
        '''
        # 1.接收数据
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        # 如果seleced没传　附默认值True
        selected = data.get('selected', True)
        # 2.验证数据(省略)
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此信息'})
        # 3.获取用户信息
        user = request.user
        if user.is_authenticated:
            # 4.登陆用户更新redis
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     4.2 更新数据
            # hash
            redis_conn.hset('carts_%s' % user.id, sku_id, count)
            # set
            if selected:
                redis_conn.sadd('selected_%s' % user.id, sku_id)
            else:
                redis_conn.srem('selected_%s' % user.id, sku_id)
            # 4.3 返回相应
            data = {
                'count': count,
                'id': sku_id,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': data})

        else:

            # 5.未登录用户更新cookie
            #     5.1 获取cookie中的数据,并进行判断
            cookie_str = request.COOKIES.get('carts')
            if cookie_str is not None:
                #         如果有数据则需要进行解码
                cookie_dict = pickle.loads(base64.b64decode(cookie_str))
            else:
                cookie_dict = {}
            # 5.2 更新数据  cart={}
            # sku_id 是否在字典列表中
            # carts = {sku_id:{count:5,selected:True}}
            if sku_id in cookie_dict:
                cookie_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            # 5.3 将字典进行编码
            cookie_data = base64.b64encode(pickle.dumps(cookie_dict))
            #     5.4 设置cookie
            data = {
                'count': count,
                'id': sku_id,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': data})
            response.set_cookie('carts', cookie_data, max_age=7 * 24 * 3600)

            #     5.5 返回相应

            return response

    def delete(self, request):
        '''
        删除购物车数据
        注意点：
        redis：
        hash数据的删除 hdel feild
        set 数据的删除　srem value
        字典数据的删除：
        del my_dict['sku_id']

        :param request:
        :return:
        '''

        user = request.user
        sku_id = json.loads(request.body.decode).get('sku_id')

        if user.is_authenticated:
            redis_conn = get_redis_connection()
            pl = redis_conn.pipeline()
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        else:
            cookie_info = request.COOKIES.get('carts')
            cookie_dict = pickle.loads(base64.b64decode(cookie_info))
            if sku_id in cookie_dict:
                del cookie_dict[sku_id]
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
