from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings


def secret_openid(openid):
    serializer = Serializer(settings.SECRET_KEY, 300)
    # serializer.dumps(数据), 返回bytes类型
    new_openid = serializer.dumps({'openid': openid})
    new_openid = new_openid.decode()
    return new_openid


def check_openid(secret_openid):
    serializer = Serializer(settings.SECRET_KEY, 300)
    try:
        data = serializer.loads(secret_openid)
    except BadData:
        return None
    else:
        return data.get('openid')
