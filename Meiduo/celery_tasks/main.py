from celery import Celery
import os
# 为celery使用django配置文件进行设置
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Meiduo.settings")

app = Celery(main='celery_task')

# 加载celery配置
app.config_from_object('celery_tasks.config')

# 自动注册celery任务
app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
