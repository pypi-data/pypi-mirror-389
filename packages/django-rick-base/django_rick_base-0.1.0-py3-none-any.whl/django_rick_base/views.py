#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cProfile import label
import logging

import time
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse


class DetailResponse(Response):
    """
    成功响应类
    用于返回成功的API响应
    """

    def __init__(self, msg="操作成功", data=None, status=200):
        response_data = {
            "code": 0,
            "msg": msg,
            "data": data
        }
        super().__init__(response_data, status=status)


class ErrorResponse(Response):
    """
    错误响应类
    用于返回错误的API响应
    """

    def __init__(self, msg="操作失败", data=None, status=400):
        response_data = {
            "code": -1,
            "msg": msg,
            "data": data
        }
        super().__init__(response_data, status=status)

from .models import UserInfo, BotHook
from .client import DingTalkClient, BotClient
from .utils import DingCallbackCrypto3
from rest_framework.parsers import JSONParser, FormParser
from .signals import *


logger = logging.getLogger("视图请求")


class DingTalkMessageSerializer(serializers.Serializer):
    """
    钉钉消息发送序列化器
    用于Swagger文档生成和参数验证
    """

    query = serializers.CharField(
        max_length=11,
        help_text="用户手机号或姓名",
        required=True,
        label="用户手机号或姓名",
    )
    content = serializers.JSONField(
        help_text="""{
            "title": "text",
            "text": "## 这是一条测试消息"
        }""",
        required=True,
        label="消息内容",
    )


class DingTalkMessageView(APIView):
    """
    钉钉消息发送视图
    提供机器人消息和群消息发送功能
    """

    permission_classes = []
    parser_classes = [JSONParser, FormParser]

    @extend_schema(
        operation_id="send_dingtalk_message",
        description="发送钉钉消息",
        summary="发送钉钉消息",
        request=DingTalkMessageSerializer,
        tags=["钉钉消息"],
    )
    def post(self, request):
        """
        发送钉钉消息
        支持机器人消息和群消息发送

        参数:
            query (str): 用户手机号
            content (str): 消息内容

        返回:
            Response: 发送结果
        """
        # 参数验证
        serializer = DingTalkMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return ErrorResponse(msg="参数验证失败", data=serializer.errors)

        query = serializer.validated_data["query"]
        content = serializer.validated_data["content"]

        try:
            if len(query) == 11:
                user_info = UserInfo.get_user_by_mobile(query)
            else:
                user_info = UserInfo.get_user_by_name(query)

            if not user_info:
                return ErrorResponse(msg=f"用户 {query} 对应的用户不存在")

            # 发送钉钉消息
            result = BotClient().send_bot_message(
                content=content, userids=[user_info.id]
            )

            logger.info(f"钉钉消息发送成功: 用户={query}, 内容={content}...")
            return DetailResponse(msg="消息发送成功", data=result)

        except Exception as e:
            logger.error(f"钉钉消息发送失败: 错误={str(e)}")
            return ErrorResponse(msg=f"消息发送失败: {str(e)}")


class DingTalkSingleMessageView(DingTalkMessageView):
    """
    单独消息发送视图
    作为 `DingTalkMessageView` 的别名，便于在路由层明确区分单发接口。

    方法:
        post: 接收手机号或姓名与消息内容，发送一对一机器人消息。
    """
    # 复用父类实现，无需改动
    pass











class DingTalkGroupMessageSerializer(serializers.Serializer):
    """
    钉钉群消息发送序列化器
    支持通过机器人 webhook 发送群消息，兼容签名校验。

    字段:
        hook_name(str, 可选): 机器人钩子名称，存在于 `BotHook` 表。
        webhook(str, 可选): 直接传入的机器人 webhook 地址。
        secret(str, 可选): 机器人密钥，用于签名(若配置了安全设置)。
        msg_type(str, 可选): 消息类型，默认 'markdown'。
        content(JSON, 必填): 实际消息内容，结构与钉钉 webhook 消息体一致。
    """

    hook_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="机器人钩子名称，优先使用数据库中的 webhook 配置",
        label="机器人钩子名称",
    )
    webhook = serializers.CharField(
        max_length=1024,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="直接传入的机器人 webhook 地址",
        label="webhook",
    )
    secret = serializers.CharField(
        max_length=1024,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="机器人密钥(若机器人开启了签名校验则必填)",
        label="secret",
    )
    msg_type = serializers.CharField(
        max_length=64,
        required=False,
        default="markdown",
        help_text="消息类型: text/markdown/link...，默认markdown",
        label="消息类型",
    )
    content = serializers.JSONField(
        help_text="钉钉群消息内容，参考webhook格式",
        required=True,
        label="消息内容",
    )

    def validate(self, attrs):
        """
        校验至少提供 `hook_name` 或 `webhook` 之一。

        返回:
            dict: 通过校验的字段字典
        """
        hook_name = attrs.get("hook_name")
        webhook = attrs.get("webhook")
        if not hook_name and not webhook:
            raise serializers.ValidationError("hook_name 与 webhook 至少提供一个")
        return attrs


class DingTalkGroupMessageView(APIView):
    """
    钉钉群消息发送视图
    通过机器人 webhook 发送群消息，支持签名校验。

    方法:
        post: 接收 webhook/secret 或 hook_name，以及消息体，完成群发。
    """

    permission_classes = []
    parser_classes = [JSONParser, FormParser]

    @extend_schema(
        operation_id="send_dingtalk_group_message",
        description="发送钉钉群消息(机器人webhook)",
        summary="发送钉钉群消息",
        request=DingTalkGroupMessageSerializer,
        tags=["钉钉消息"],
    )
    def post(self, request: Request):
        """
        发送群消息

        参数:
            hook_name(str): 机器人钩子名称(优先)
            webhook(str): 机器人webhook地址
            secret(str): 机器人密钥(可选)
            msg_type(str): 消息类型，默认markdown
            content(JSON): 消息内容

        返回:
            Response: 发送结果
        """
        serializer = DingTalkGroupMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return ErrorResponse(msg="参数验证失败", data=serializer.errors)

        hook_name = serializer.validated_data.get("hook_name")
        webhook = serializer.validated_data.get("webhook")
        secret = serializer.validated_data.get("secret")
        msg_type = serializer.validated_data.get("msg_type")
        content = serializer.validated_data.get("content")

        try:
            # 优先通过 hook_name 获取配置
            if hook_name:
                hook = BotHook.objects.filter(hook_name=hook_name).first()
                if not hook:
                    return ErrorResponse(msg=f"机器人钩子不存在: {hook_name}")
                webhook = hook.webhook
                # 若请求未显式传入secret，则使用数据库中的secret
                secret = secret or hook.secret

            if not webhook:
                return ErrorResponse(msg="webhook未提供，无法发送群消息")

            result = BotClient().send_group_message_by_webhook(
                webhook=webhook, secret=secret, content=content, msg_type=msg_type
            )
            logger.info(f"钉钉群消息发送成功: hook={hook_name or 'raw'}, 类型={msg_type}")
            return DetailResponse(msg="群消息发送成功", data=result)

        except Exception as e:
            logger.error(f"钉钉群消息发送失败: 错误={str(e)}")
            return ErrorResponse(msg=f"群消息发送失败: {str(e)}")


@csrf_exempt
@api_view(["POST", "GET"])
def callback(request):
    """
    处理钉钉回调请求
    钉钉事件订阅回调接口，用于接收钉钉推送的事件消息
    """
    try:
        logger.info(f"接收到钉钉callback请求: method={request.method}")
        _crypto = DingCallbackCrypto3()

        if request.method == "POST":
            # 获取URL参数
            signature = request.GET.get("signature")
            timestamp = request.GET.get("timestamp")
            nonce = request.GET.get("nonce")

            # 获取请求体数据
            import json

            try:
                json_data = json.loads(request.body.decode("utf-8"))
                encrypt = json_data.get("encrypt")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"解析请求体失败: {e}")
                return Response({"code": -1, "msg": "请求体格式错误"})

            # 解密消息
            if signature and timestamp and nonce and encrypt:
                try:
                    response = _crypto.getDecryptMsg(
                        signature, timestamp, nonce, encrypt
                    )
                    logger.info(f"钉钉callback解密成功: {response}")
                    
                    # 发送消息接收通知，供其他APP选择接收处理
                    from .signals import NotificationManager
                    NotificationManager.send_message_received_notification(
                        sender=callback,
                        message_type="dingtalk_callback",
                        message=response
                    )
                    
                except Exception as e:
                    logger.error(f"钉钉callback解密失败: {e}")
                    return Response({"code": -1, "msg": "消息解密失败"})
            else:
                logger.warning("钉钉callback参数不完整")
                return Response({"code": -1, "msg": "参数不完整"})
        else:
            logger.info("接收到钉钉callback GET请求")

        # 返回加密的成功响应
        encrypted_response = _crypto.getEncryptedMap("success")
        return Response(encrypted_response)

    except Exception as e:
        logger.error(f"处理钉钉callback请求时发生错误: {e}")
        return Response({"code": -1, "msg": "处理失败"})


@api_view(["GET"])
def health_check(request):
    """
    健康检查接口
    """
    client = DingTalkClient()
    if client.access_token:
        return DetailResponse(
            msg="钉钉应用运行正常",
            data={
                "status": "ok",
                "timestamp": int(time.time()),
            },
        )
    return ErrorResponse(msg="钉钉应用运行异常")
