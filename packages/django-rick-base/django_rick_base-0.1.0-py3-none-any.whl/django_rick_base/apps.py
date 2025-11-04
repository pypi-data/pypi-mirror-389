from django.apps import AppConfig
import logging

logger = logging.getLogger("初始化钉钉")


class DingtalkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_rick_base"
    verbose_name = "钉钉"

    # 启用信号量
    def ready(self):
        import django_rick_base.signals

        logger.info(f"初始化钉钉信号量 {django_rick_base.signals.__name__}")

        from django.conf import settings

        # 检查是否配置了DINGTALK_APP_KEY和DINGTALK_APP_SECRET
        # 检查是否配置了DINGTALK_CLIENT_ID
        if not (
            hasattr(settings, "DINGTALK_APP_KEY")
            and hasattr(settings, "DINGTALK_APP_SECRET")
        ):
            raise ValueError(
                "DINGTALK_APP_KEY or DINGTALK_APP_SECRET not set in settings"
            )
