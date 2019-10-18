# 生产者
from random import random
from libs.yuntongxun.sms import CCP
from django_redis import get_redis_connection
# 导入实例对象用于装饰任务
from celery_tasks.main import app


@app.task(bind=True, name='send_sms_code', retry_backoff=3)
def send_sms_code(self,mobile, sms_code):
    try:
        ccp = CCP()
        send_ret = ccp.send_template_sms('13581824252', [sms_code, 5], 1)
    except Exception as e:
        raise self.retry(exc=e, max_retries=3)
    if send_ret!=0:
        # 有异常自动重试三次
        raise self.retry(exc=Exception('发送短信失败'), max_retries=3)
    else:
        redis_conn = get_redis_connection('message_code')
        redis_conn.setex('sms_%s' % mobile, 3000, sms_code)
        #  设置发送 flag 有效期60秒 用于判断和控制用户频繁调用接口
        redis_conn.setex('send_flag_%s' % mobile, 60, 1)

    return send_ret
