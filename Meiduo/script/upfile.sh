#!/usr/bin/python
#创建对象并指明配置文件
from fdfs_client.client import Fdfs_client
client = Fdfs_client('utils/fastdfs/client.conf')
# 调用上传文件方法
client.upload_by_filename('/home/python/Desktop/images/0.jpg')