from django.apps import AppConfig


class DjangoAdminLogentryExtensionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_admin_logentry_extension"

    def ready(self):
        # 注意：
        # 这个引用不能放在函数外面
        # patch_all中有引用models
        # 但models只有在app ready后才可以使用
        # 该引用必须放在函数内
        # 不要因为代码静态检查等原因，将引用放到函数外
        from .monkey import patch_all  # noqa

        patch_all()
