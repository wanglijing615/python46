# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-10-20 13:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0002_oauthqquser_email_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oauthqquser',
            name='email_active',
        ),
    ]
