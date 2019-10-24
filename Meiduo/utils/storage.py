"""
Django自定义文件存储类
1.您的自定义存储系统必须是的子类 django.core.files.storage.Storage
2.Django必须能够在没有任何参数的情况下实例化您的存储系统。
    这意味着任何设置都应来自django.conf.settings
3.您的存储类必须实现_open()和_save() 方法，以及适用于您的存储类的任何其他方法

"""
from django.core.files.storage import Storage
from django.conf import settings

class MyStorage(Storage):

    # def __init__(self, option=None):
    #     if not option:
    #         option = settings.CUSTOM_STORAGE_OPTIONS

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content, max_length=None):
        pass

    def url(self, name):
        # 默认url 是返回name
        # group1/M00/00/01/CtM3BVrLmc-AJdVSAAEI5Wm7zaw8639396
        # http://ip:port/ + name
        return "http://192.168.229.148:8888/" + name




# class Person(object):
#
#     def __init__(self,name=None):
#         name=settings.DEFAULT_NAME
#         self.name=name

# p = Person()
# p.name='itcast'

# p = Person(name='itcast')
# p2=Person()


