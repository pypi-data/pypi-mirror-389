from django.db import models


# 这些是Django默认的动作标志定义
#
# 新增数据对象
# ADDITION = 1
#
# 修改数据对象
# CHANGE = 2
#
# 删除数据对象
# DELETION = 3
#
# 这些是扩展的动作标志
#
# 浏览数据对象列表
BROWSING = 10
#
# 查看数据对象详情
READING = 11
#
# 导出数据对象
EXPORTING = 12
#
# 导入数据对象
IMPORTING = 13
#
# 用户登录
LOGIN = 21
#
# 用户注销
LOGOUT = 22
#
# 额外的动作标识
ACTION_FLAG_EXT_CHOICES = [
    (BROWSING, "浏览"),
    (READING, "查看"),
    (EXPORTING, "导出"),
    (IMPORTING, "导入"),
    (LOGIN, "登录"),
    (LOGOUT, "登出"),
]
