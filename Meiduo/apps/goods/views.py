import datetime
import json
import pickle

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.utils import timezone
from django_redis import get_redis_connection

from apps.goods.models import GoodsCategory, SKU, GoodsVisitCount
from django.shortcuts import render
from django.views import View
from apps.contents.utils import get_categories
from apps.goods.models import SKU, GoodsCategory
from apps.goods.utls import get_breadcrumb
from utils.response_code import RETCODE

"""
href="{{ url('goods:list', args=(category.id, page_num)) }}?sort=default"
/list/(?P<category_id>\d+)/(?P<page_num>\d+)/?sort=排序方式
# 按照商品创建时间排序
http://www.meiduo.site:8000/list/115/1/?sort=default
# 按照商品价格由低到高排序
http://www.meiduo.site:8000/list/115/1/?sort=price
# 按照商品销量由高到低排序
http://www.meiduo.site:8000/list/115/1/?sort=hot
"""


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id, page_num):
        """提供商品列表页"""

        # 1.判断category_id是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseBadRequest('category参数错误')
            # 2.查询商品频道分类,查询面包屑导航
        categories = get_categories()
        breadcrumb = get_breadcrumb(category)

        # 3.根据sort方式 确认不同的排序字段,传递不同的数据进行数据排序
        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            # 价格 升序
            sort_field = 'price'
        elif sort == 'hot':
            #  人气 按照销量降序
            sort_field = '-sales'
        else:
            # 默认按照创建时间升序
            sort_field = 'create_time'
        # 根据排序字段查出所有数据
        datas_obj = SKU.objects.filter(category=category).order_by(sort_field)

        # 4.根据当前页号,每次返回5条
        # ① 创建分页器
        page_obj = Paginator(datas_obj, 5)
        try:
            # ② 获取指定页面的数据
            datas = page_obj.page(page_num)
        except EmptyPage:
            # 如果page_num不正确，默认给用户404
            return HttpResponseNotFound('empty page')
        # ③获取列表页总页数
        total_page = page_obj.num_pages

        # 5.组装渲染数据并返回响应

        # 渲染页面
        context = {
            'categories': categories,  # 频道分类
            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': datas,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request, 'list.html', context)


"""
/hot/(?P<category_id>\d+)/

"""


class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行JSON数据"""

        # 热销排行:根据sales降序 取两个数据
        datas_obj = SKU.objects.filter(category_id=category_id).order_by('-sales')[0:2]

        # 根据销量倒序
        # skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        hot_skus = []
        for sku in datas_obj:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({'code': 0, 'errmsg': 'OK', 'hot_skus': hot_skus})


# /detail/(?P<sku_id>\d+)/



class DetailView(View):
    def get(self, request, sku_id):

        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }

        return render(request, 'detail.html', context)


# l;/(?P<category_id>\d+)/

class DetailVisitView(View):
    """详情页分类商品访问量"""

    def post(self, request, category_id):
        """记录分类商品访问量"""

        # 1.查询商品信息是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseBadRequest('商品不存在')
        # 2.查询今天是否已创建过统计记录 没有则创建,有则修改
        # ① 构建今天日期变量
        # t = timezone.localtime()
        # today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)
        # today_date = datetime.datetime.strptime(today_str, '%Y-%m-%d')
        today_date = timezone.localdate()
        try:
            # 根据外键字段关联查询数据
            count_data = category.goodsvisitcount_set.get(date=today_date)
        except GoodsVisitCount.DoesNotExist:
            # count_obj = GoodsVisitCount()
            # count_obj.category = category
            # count_obj.count += 1
            # count_obj.save()
            GoodsVisitCount.objects.create(
                category=category,
                date=today_date,
                count=1
            )
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:
            count_data.count += 1
            count_data.save()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class UserBrowseHistory(LoginRequiredMixin, View):
    """用户浏览记录"""

    def post(self, request):
        """保存用户浏览记录"""
        # 获取浏览商品id
        sku_id = json.loads(request.body.decode()).get('sku_id')
        # 判断商品信息是否存在,如果不存在返回错误
        if not SKU.objects.filter(id=sku_id):
            return HttpResponseBadRequest('商品不存在')
        else:
            # 查询用户是否存在浏览量记录,如果不存在 创建浏览记录 并返回响应
            redis_conn = get_redis_connection('history')
            # 创建Redis管道
            pl = redis_conn.pipeline()
            user_id = request.user.id

            # 将Redis请求添加到队列
            # 增加记录时,最多5个数据,多余的删除
            # 先去重
            pl.lrem('history_%s' % user_id, 0, sku_id)
            # 再存储
            pl.lpush('history_%s' % user_id, sku_id)
            # 最后截取
            pl.ltrim('history_%s' % user_id, 0, 4)
            # 执行管道
            pl.execute()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

    def get(self, request):
        """获取用户浏览记录"""
        # 判断用户是否登陆,只有登陆用户可以查看浏览记录
        # 登陆用户查询数据
        user_id = request.user.id
        redis_conn = get_redis_connection('history')
        # pl = redis_conn.pipeline()
        # history_list = pl.lrange('history_%s' % user_id, 0, -1)
        # pl.execute()
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        # 组装数据
        data_list = []
        for sku in sku_ids:
            sku_obj = SKU.objects.get(id=sku)
            data_list.append({
                'id': sku_obj.id,
                'name': sku_obj.name,
                'default_image_url': sku_obj.default_image.url,
                'price': sku_obj.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'skus': data_list})
