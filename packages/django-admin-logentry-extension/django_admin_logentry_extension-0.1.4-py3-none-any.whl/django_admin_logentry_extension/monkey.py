import json
import logging
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.utils import unquote
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.options import get_content_type_for_model
from django.contrib import auth
from django.contrib.auth import sensitive_variables
from django.contrib.auth import get_user_model

from .models import ACTION_FLAG_EXT_CHOICES
from .models import BROWSING
from .models import READING
from .models import LOGIN
from .models import LOGOUT
from .models import IMPORTING
from .models import EXPORTING
from .utils import add_extra_action_flags


_logger = logging.getLogger(__name__)


def patch_all():
    action_flag_patch()
    change_message_patch()
    changelist_view_patch()
    changeform_view_patch()
    login_patch()
    logout_patch()
    # django-import-export补丁
    import_export_patch()


def action_flag_patch():
    """添加额外的动作标识"""
    add_extra_action_flags(ACTION_FLAG_EXT_CHOICES)


def change_message_patch():
    """修改change_message显示为操作详情。"""
    change_message_field = LogEntry._meta.get_field("change_message")
    change_message_field.verbose_name = "操作详情"
    change_message_field._verbose_name = "操作详情"


def changelist_view_patch():
    """拦截changelist_view，进行操作日志记录。"""
    changelist_view_original = ModelAdmin.changelist_view

    @csrf_protect_m
    def changelist_view_new(self, request, extra_context=None):
        LogEntry.objects.create(
            content_type_id=get_content_type_for_model(self.model).pk,
            object_id=None,
            object_repr="数据列表",
            change_message=json.dumps(dict(request.GET), ensure_ascii=False),
            action_flag=BROWSING,
            user=request.user.pk and request.user or None,
        )
        return changelist_view_original(self, request, extra_context)

    ModelAdmin.changelist_view = changelist_view_new


def changeform_view_patch():
    """拦截changeform_view，进行操作日志记录。"""
    changeform_view_original = ModelAdmin.changeform_view

    @csrf_protect_m
    def changeform_view_new(
        self, request, object_id=None, form_url="", extra_context=None
    ):
        if request.method == "GET" and object_id:
            obj = self.get_object(request, unquote(object_id))
            LogEntry.objects.create(
                content_type_id=get_content_type_for_model(self.model).pk,
                object_id=object_id,
                object_repr=str(obj),
                action_flag=READING,
                user=request.user.pk and request.user or None,
            )
        return changeform_view_original(
            self, request, object_id, form_url, extra_context
        )

    ModelAdmin.changeform_view = changeform_view_new


def login_patch():
    """拦截admin登录方法，进行操作日志记录。"""
    authenticate_orignal = auth.authenticate

    @sensitive_variables("credentials")
    def authenticate_new(request=None, **credentials):
        # 获取登录用户信息
        # 因为操作日志必须强关联用户
        # 如果不是注册用户的登录请求
        # 则无法将该登录事件绑定到用户
        # 所以不记录非注册用户的登录失败事件
        User = get_user_model()
        username = credentials.get("username", None)
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

        error = None
        result = None
        login_status = "未知"
        try:
            result = authenticate_orignal(request, **credentials)
            if result:
                login_status = "成功"
            else:
                login_status = "失败"
        except Exception as err:
            error = err
            login_status = "异常"

        if user:
            LogEntry.objects.create(
                content_type_id=get_content_type_for_model(User).pk,
                object_id=username,
                object_repr=f"用户{username}登录{login_status}",
                action_flag=LOGIN,
                user=user,
            )
        else:
            _logger.warning(f"非注册用户登录失败：{username}")

        if error:
            raise error
        else:
            return result

    auth.authenticate = authenticate_new


def logout_patch():
    """拦截admin登出方法，进行操作日志记录。"""
    logout_original = auth.logout

    def logout_new(request):
        if request.user and request.user.pk:
            User = get_user_model()
            username = request.user.username
            LogEntry.objects.create(
                content_type_id=get_content_type_for_model(User).pk,
                object_id=username,
                object_repr=f"用户{username}登出",
                action_flag=LOGOUT,
                user=request.user,
            )
        return logout_original(request)

    auth.logout = logout_new


def import_export_patch():
    """django-import-export插件的补丁"""
    import_export_export_patch()
    import_export_import_patch()


def import_export_export_patch():
    try:
        # 如果安装了import_export，进行拦截并进行操作日志记录
        from import_export.admin import ExportMixin

        export_action_original = ExportMixin.export_action

        def export_action_new(self, request, *args, **kwargs):
            post_data = dict(request.POST)
            if "csrfmiddlewaretoken" in post_data:
                del post_data["csrfmiddlewaretoken"]
            LogEntry.objects.create(
                content_type_id=get_content_type_for_model(self.model).pk,
                object_id=None,
                object_repr="",
                action_flag=EXPORTING,
                change_message=json.dumps(
                    {
                        "request_params": dict(request.GET),
                        "post_data": post_data,
                    },
                    ensure_ascii=False,
                ),
                user=request.user,
            )
            return export_action_original(self, request, *args, **kwargs)

        ExportMixin.export_action = export_action_new
    except ImportError:
        # 如果没有安装import_export，则忽略
        pass


def import_export_import_patch():
    try:
        # 如果安装了import_export，进行拦截并进行操作日志记录
        from import_export.admin import ImportMixin

        import_action_original = ImportMixin.import_action

        def import_action_new(self, request, *args, **kwargs):
            post_data = dict(request.POST)
            if "csrfmiddlewaretoken" in post_data:
                del post_data["csrfmiddlewaretoken"]
            LogEntry.objects.create(
                content_type_id=get_content_type_for_model(self.model).pk,
                object_id=None,
                object_repr="",
                action_flag=IMPORTING,
                change_message=json.dumps(
                    {
                        "request_params": dict(request.GET),
                        "post_data": post_data,
                    },
                    ensure_ascii=False,
                ),
                user=request.user,
            )
            return import_action_original(self, request, *args, **kwargs)

        ImportMixin.import_action = import_action_new
    except ImportError:
        # 如果没有安装import_export，则忽略
        pass
