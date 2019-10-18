import re

from django.contrib.auth.backends import ModelBackend
from apps.users.models import UserModel
import logging

logger = logging.getLogger('django')


# 封装和抽取 判断用户使用用户名还是手机号登陆并返回user
def get_user_by_usernamemobile(username):
    try:
        if re.match(r'1[3-9]\d{9}', username):
            user = UserModel.objects.get(mobile=username)
        else:
            user = UserModel.objects.get(username=username)
    except Exception as e:
        logger.error(e)
        return None
    return user


class UsernameMobile(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # try:
        #     if re.match(r'1[3-9]\d{9}',username):
        #         user = UserModel.objects.get(mobile=username)
        #     else:
        #         user = UserModel.objects.get(username=username)
        # except Exception as e:
        #     logger.error(e)
        #     return None
        user = get_user_by_usernamemobile(username)
        if user is not None and user.check_password(password):
            return user
