from django.core.mail import send_mail

from celery_tasks.main import app
from utils.generate_url import generic_acive_email_url


@app.task(bind=True)
def send_email(self, user_id, email):
    # subject, message, from_email, recipient_list,
    # subject        主题
    subject = '美多商场激活邮件'
    # message,       内容
    message = ''
    # from_email,  谁发的
    from_email = '美多商城<qi_rui_hua@163.com>'
    # recipient_list,  收件人列表
    recipient_list = [email]
    # 激活链接
    active_url = generic_acive_email_url(user_id=user_id, email=email)
    html_mesage = '<p>尊敬的用户您好！</p>' \
                  '<p>感谢您使用美多商城。</p>' \
                  '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                  '<p><a href="%s">%s<a></p>' % (email, active_url, active_url)

    try:
        send_mail(subject=subject,
                  message=message,
                  from_email=from_email,
                  recipient_list=recipient_list,
                  html_message=html_mesage)
    except Exception as e:

        raise self.retry(exc=e, max_retries=3)
