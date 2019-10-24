from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from Meiduo import settings


def generic_acive_email_url(user_id, email):
    '''生成激活链接 '''
    # 加密 01 创建加密实例对象
    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    data = {'user_id': user_id, 'email': email}
    token = serializer.dumps(data).decode()
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    return verify_url


def check_active_email_url(token):
    s = Serializer(settings.SECRET_KEY, expires_in=3600)
    try:
        data = s.loads(token)
    except BadData:
        return None
    else:
        return data
