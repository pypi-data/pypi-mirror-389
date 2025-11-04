from venv import logger
from django.db import models
import time
from .client import UserClient


class BaseModel(models.Model):
    # 基础模型，所有模型都继承自该模型,主要记录创建时间和更新时间用于控制更新
    create_time = models.DateTimeField(
        verbose_name="创建时间", auto_now_add=True, null=True, blank=True
    )
    update_time = models.DateTimeField(
        verbose_name="更新时间", auto_now=True, null=True, blank=True
    )
    sync_status = models.BooleanField(
        verbose_name="同步状态", default=False, null=True, blank=True
    )

    class Meta:
        abstract = True


class UserInfo(BaseModel):
    id = models.CharField(max_length=255, verbose_name="钉钉用户id", primary_key=True)
    mobile = models.CharField(
        max_length=255, verbose_name="手机号", null=True, blank=True
    )
    name = models.CharField(max_length=255, verbose_name="姓名", null=True, blank=True)
    avatar = models.CharField(
        max_length=255, verbose_name="头像", null=True, blank=True
    )
    email = models.CharField(max_length=255, verbose_name="邮箱", null=True, blank=True)
    job_number = models.CharField(
        max_length=255, verbose_name="工号", null=True, blank=True
    )
    department = models.CharField(
        max_length=255, verbose_name="部门", null=True, blank=True
    )
    position = models.CharField(
        max_length=255, verbose_name="职位", null=True, blank=True
    )
    extra = models.TextField(
        verbose_name="全部信息", default="{}", null=True, blank=True
    )
    access_token = models.CharField(
        max_length=255, verbose_name="access_token", null=True, blank=True
    )
    expires_in = models.IntegerField(
        verbose_name="过期时间", default=0, null=True, blank=True
    )
    refresh_token = models.CharField(
        max_length=255, verbose_name="refresh_token", null=True, blank=True
    )

    class Meta:
        db_table = "dingtalk_user_info"
        verbose_name = "钉钉用户信息"
        verbose_name_plural = "钉钉用户信息"

    def __str__(self):
        return f"钉钉用户 - {self.name}({self.mobile})"

    def is_token_valid(self):
        """
        检查用户token是否有效
        """
        return self.expires_in > time.time()

    def get_access_token(self):
        """
        获取有效的用户access_token
        """
        if self.is_token_valid():
            return self.access_token
        return None

    @classmethod
    def get_user_by_mobile(cls, mobile):
        """
        根据手机号获取用户信息
        """
        user_info = cls.objects.filter(mobile=mobile).first()
        if user_info:
            return user_info
        client = UserClient()
        user_info = client.get_user_by_mobile(mobile)
        if user_info.get("userid", "") == "":
            return None
        user = UserInfo.objects.create(
            mobile=mobile,
            id=user_info.get("userid", ""),
        )
        user.save()
        return user

    @classmethod
    def get_user_by_name(cls, name):
        """
        根据姓名获取用户信息
        """
        user_info = cls.objects.filter(name=name).first()
        if user_info:
            return user_info
        client = UserClient()
        userids = client.get_user_by_name(name)
        if not userids:
            logger.error(f"根据姓名获取用户失败: {name}")
            return None
        for _id in userids:
            user = UserInfo.objects.create(
                name=name,
                id=_id,
            )
            user.save()

        return cls.get_user_by_name(name)


class Department(BaseModel):
    id = models.CharField(max_length=255, verbose_name="部门id", primary_key=True)
    name = models.CharField(
        max_length=255, verbose_name="部门名称", null=True, blank=True
    )
    parent_id = models.CharField(
        max_length=255, verbose_name="父部门id", null=True, blank=True
    )
    order = models.IntegerField(
        verbose_name="部门排序", default=0, null=True, blank=True
    )
    extra = models.TextField(
        verbose_name="全部信息", default="{}", null=True, blank=True
    )

    class Meta:
        db_table = "dingtalk_department"
        verbose_name = "钉钉部门"
        verbose_name_plural = "钉钉部门"

    def __str__(self):
        return f"钉钉部门 - {self.name}({self.id})"


class BotHook(models.Model):
    hook_name = models.CharField(
        max_length=255, verbose_name="机器人名称", null=True, blank=True
    )
    webhook = models.CharField(
        max_length=255, verbose_name="机器人webhook", null=True, blank=True
    )
    secret = models.CharField(
        max_length=255, verbose_name="机器人secret", null=True, blank=True
    )
    extra = models.TextField(
        verbose_name="全部信息", default="{}", null=True, blank=True
    )

    class Meta:
        db_table = "dingtalk_bot_hook"
        verbose_name = "钉钉机器人钩子"
        verbose_name_plural = "钉钉机器人钩子"

    def __str__(self):
        return f"钉钉机器人钩子 - {self.hook_name}({self.pk})"
