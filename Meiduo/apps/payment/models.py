from django.db import models

from django.db import models
from apps.orders.models import OrderInfo
from utils.models import BaseModel

class Payment(BaseModel):
    """支付信息"""
    # 关联订单号
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, verbose_name='订单')
    # 支付宝交易流水号
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="支付编号")

    class Meta:
        db_table = 'tb_payment'
        verbose_name = '支付信息'
        verbose_name_plural = verbose_name
