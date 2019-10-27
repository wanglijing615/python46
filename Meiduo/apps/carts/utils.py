# 合并购物车

import base64
import pickle
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    '''
    如果cookie中的数据redis已存在，则用cookie的数据覆盖redis存在的数据
    '''
    # 获取cookie数据
    cookie_data = request.COOKIES.get('carts')
    if cookie_data is not None:
        # redis数据结构: hash carts_user.id, count,1
        # set: (sku_id,sku_id)
        # 取redis的数据
        redis_conn = get_redis_connection('carts')
        # carts_data = redis_conn.hmget('carts_%s' % user.id)
        selected_data = redis_conn.smembers('selected_%s' % user.id)
        # 从reids获取的数据为bytes类型,需进行转换组装数据
        redis_id_list = []
        for id in selected_data:
            redis_id_list.append(int(id))

        cookie_dict = pickle.loads(base64.b64decode(cookie_data))
        # {sku_id:{'count':2,'selected':True},}
        # cookie_select_id_list = []
        # cookie_unselected_id_list = []
        for sku_id, value in cookie_dict.items():
            redis_conn.hset('carts_%s' % user.id, sku_id, int(value['count']))
            if value['selected']:
                redis_conn.sadd('selected_%s' % user.id, sku_id)
                # cookie_unselected_id_list.append(sku_id)
            else:
                redis_conn.srem('selected_%s' % user.id, sku_id)
                # cookie_select_id_list.append(sku_id)

        # 删除cookie数据
        response.delete_cookie('carts')
    return response
