# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-10-20 13:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermodel',
            name='email_active',
            field=models.BooleanField(default=False, max_length=2, verbose_name='邮箱激活状态'),
        ),
    ]
