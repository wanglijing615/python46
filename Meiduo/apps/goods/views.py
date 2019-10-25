from django.core.paginator import Paginator, EmptyPage
from django.db.models.sql import constants
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.contents.utils import get_categories
from apps.goods.models import GoodsCategory, SKU
from apps.goods.utls import get_breadcrumb

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
