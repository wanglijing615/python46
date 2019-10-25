"""
路径参数category_id是商品第三级分类
通过category_id可以得到category对象 ,通过category对象可以得到属性字段parent
通过category.parent可以判断当前是几级类别,不同级别构造对应级别以上的数据返回即可
一级 parent为None
三级 没有子级,因此subs.count=0
"""
def get_breadcrumb(category):
    """
    获取面包屑导航
    :param category: 商品类别
    :return: 面包屑导航字典
    """
    # 组装数据,返回数据为各级别种类名称
    breadcrumb = dict(
        cat1='',
        cat2='',
        cat3=''
    )
    if category.parent is None:
        # 当前类别为一级类别
        breadcrumb['cat1'] = category
    elif category.subs.count() == 0:
        # 当前类别为三级
        breadcrumb['cat3'] = category
        cat2 = category.parent
        breadcrumb['cat2'] = cat2
        breadcrumb['cat1'] = cat2.parent
    else:
        # 当前类别为二级
        breadcrumb['cat2'] = category
        breadcrumb['cat1'] = category.parent

    return breadcrumb
