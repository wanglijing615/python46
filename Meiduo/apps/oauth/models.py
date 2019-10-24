from django.db import models

# Create your models here.
from django.db import models
from utils.models import BaseModel


class OAuthQQUser(BaseModel):
    """QQ登录用户数据"""
    user = models.ForeignKey('users.UserModel', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)
    # email_active = models.BooleanField(max_length=2, verbose_name='邮箱激活状态', default=False)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name
