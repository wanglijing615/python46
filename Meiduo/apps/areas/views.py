import json
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.areas.models import Area
from apps.users.models import Address
import logging

from utils.response_code import RETCODE

logger = logging.getLogger('django')


# class SiteView(LoginRequiredMixin, View):
#     """收货地址页"""
#
#     def get(self, request):
#         return render(request, 'user_center_site.html')


class AreasView(View):
    """ 获取省 市 区县数据"""

    def get(self, request):
        # 请求url this.host + '/areas/?area_id=' + this.form_address.city_id;
        # 1. 获取parent_id
        parent_id = request.GET.get('area_id')
        # 2. parent_id None 查询省,否则查询 市 区县
        if parent_id is None:
            # 3. 查询缓存 缓存没有查询db 并设置缓存
            province_catch = cache.get('province_catch')
            if province_catch is None:
                province_obj = Area.objects.filter(parent=None)
                province_catch = []
                for province in province_obj:
                    province_dict = {
                        'id': province.id,
                        'name': province.name
                    }
                    province_catch.append(province_dict)
                    #     设置缓存
                cache.set('province_catch', province_catch, 24 * 3600)
            return JsonResponse({'code': 0, 'province_list': province_catch})

        else:
            try:
                province_catch = cache.get('city_%s' % parent_id)
            except Exception as e:
                print(e)
            if province_catch is None:
                try:
                    province_obj = Area.objects.get(id=parent_id)
                    # 查询区 县
                    cities = province_obj.subs.all()
                except Exception as e:
                    return JsonResponse({'code': 0, 'subs': []})
                province_catch = []
                for city in cities:
                    province_catch.append({
                        'id': city.id,
                        'name': city.name
                    })
                # 设置缓存
                cache.set('city_%s' % parent_id, province_catch, 24 * 3600)
                return JsonResponse({'code': 0, 'subs': province_catch})
            else:
                return JsonResponse({'code': 0, 'subs': province_catch})


class AddressCreateView(LoginRequiredMixin, View):
    """新增收货地址"""

    def post(self, request):
        # 1.判断用户已添加的地址数量 if >20 则响应已达到添加上限
        count = request.user.addresses.count()
        if count >= 20:
            return JsonResponse({'code': 4101, 'errmsg': '超过地址数量上限'})
            # 2.接收用户数据参数
        json_dict = json.loads((request.body.decode()))
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 3.数据检验
        # ① 必填校验: 收货人 所在地区 详细地址 手机
        if not all([]):
            return JsonResponse({{'code': 4102, 'errmsg': '缺少必填参数'}})
            # ② 数据格式: 手机 固话 邮箱
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 4007, 'errmsg': '手机号填写错误'})

        # ③非必填项 如果有值则校验
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 5002, 'errmsg': '固话填写错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 5001, 'errmsg': '邮箱填写错误'})
        # 4.保存地址信息 入库 涉及到数据库的操作一定要加异常try
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            return JsonResponse({'code': 4103, 'errmsg': '数据库操作异常'})
        ### 如果当前用户还每有默认地址 则设置此次添加的地址为默认地址
        if not request.user.default_address:
            request.user.default_address = address
            request.user.save()
        # 5.返回响应
        # 返回数据
        address_dict = {"id": address.id,
                        "title": address.title,
                        "receiver": address.receiver,
                        "province": address.province.name,
                        "city": address.city.name,
                        "district": address.district.name,
                        "place": address.place,
                        "mobile": address.mobile,
                        "tel": address.tel,
                        "email": address.email}

        return JsonResponse({'code': 0, 'errmsg': '新增地址成功', 'address': address_dict})


class AddressView(LoginRequiredMixin, View):
    """展示用户收货地址"""

    def get(self, request):
        # 获取用户地址数据,注意地址状态为未删除的
        login_user = request.user
        try:
            addresses = Address.objects.filter(user=login_user, is_deleted=False)
        except Exception as e:
            return JsonResponse({'code': 4103, 'errmsg': '数据库操作异常'})
        # 拼装用户数据成字典格式
        address_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_list.append(address_dict)
            # 组织返回渲染content
        content = {
            'default_address_id': request.user.default_address_id,
            'addresses': address_list
        }
        return render(request, 'user_center_site.html', context=content)


class UpdateAddressView(View):
    """修改收货地址"""

    # url = this.host + '/addresses/' + this.addresses[this.editing_address_index].id + '/';

    def put(self, request, address_id):
        # 获取数据
        json_dict = json.loads((request.body.decode()))
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 验证数据
        # ① 必填校验: 收货人 所在地区 详细地址 手机
        if not all([]):
            return JsonResponse({{'code': 4102, 'errmsg': '缺少必填参数'}})
            # ② 数据格式: 手机 固话 邮箱
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 4007, 'errmsg': '手机号填写错误'})

        # ③非必填项 如果有值则校验
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 5002, 'errmsg': '固话填写错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 5001, 'errmsg': '邮箱填写错误'})
        # 更新数据
        try:

            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 4101, 'errmsg': '更新地址失败'})
            # 构造响应数据,返回响应
        address = Address.objects.get(id=address_id)
        address_dict = {"id": address.id,
                        "title": address.title,
                        "receiver": address.receiver,
                        "province": address.province.name,
                        "city": address.city.name,
                        "district": address.district.name,
                        "place": address.place,
                        "mobile": address.mobile,
                        "tel": address.tel,
                        "email": address.email}

        return JsonResponse({'code': 0, 'errmsg': '修改地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        # /addresses/(?P<address_id>\d+)/

        # 校验地址是否存在
        try:
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Address.DoesNotExist:
            return JsonResponse({'code': 0, 'errmsg': '地址信息异常,删除失败'})
        else:
            return JsonResponse({'code': 0, 'errmsg': '删除地址成功'})


class DefaultAddressView(LoginRequiredMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})