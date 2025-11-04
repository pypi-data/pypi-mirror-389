#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
from typing import Dict, Optional, Any
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("CLIENT客户端")


class DingTalkClient:
    """
    钉钉API客户端
    提供钉钉相关API的封装调用
    """

    def __init__(self, key: str = None, secret: str = None):
        self.key = key or settings.DINGTALK_APP_KEY
        self.secret = secret or settings.DINGTALK_APP_SECRET
        self.client_id = getattr(settings, "DINGTALK_CLIENT_ID", None)
        self._access_token = None

    @property
    def access_token(self):
        """获取access_token属性，自动处理缓存"""
        if not self._access_token:
            self._access_token = self.get_token()
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        """设置access_token属性"""
        self._access_token = value

    def get_token(self):
        """
        获取access_token，使用缓存自动管理token的获取和过期

        Returns:
            access_token字符串，失败返回None
        """
        try:
            # 生成缓存键
            cache_key = f"dingtalk_token_{self.key}"

            # 尝试从缓存获取token
            cached_token = cache.get(cache_key)
            if cached_token:
                logger.info("从缓存获取access_token成功")
                return cached_token

            # 缓存中没有token，重新获取
            logger.info("缓存中无token，重新获取access_token")

            # 使用标准API获取token
            url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
            params = {"appKey": self.key, "appSecret": self.secret}
            response = requests.post(url, json=params)
            # response.raise_for_status()
            result = response.json()
            logger.info(f"获取access_token响应: {result}")
            # 检查是否成功获取到access_token
            access_token = result.get("accessToken")
            if access_token:
                expires_in = result.get("expireIn", 7200)

                # 将token存入缓存，设置过期时间为实际过期时间减去5分钟的缓冲时间
                cache_timeout = max(expires_in - 300, 60)  # 至少缓存1分钟
                cache.set(cache_key, access_token, cache_timeout)

                logger.info(f"获取access_token成功，已缓存{cache_timeout}秒")
                return access_token
            else:
                error_msg = result.get("errmsg", result.get("message", "未知错误"))
                logger.error(f"获取access_token失败: {error_msg}")
                return None

        except Exception as e:
            logger.error(f"获取access_token异常: {str(e)}")
            return None


class UserClient(DingTalkClient):
    """
    用户管理客户端
    """

    def get_user_by_mobile(self, mobile):
        """
        根据手机号获取用户信息

        Args:
            mobile: 手机号
            access_token: 访问令牌，如果不传则使用self.token

        Returns:
            用户信息字典
        """
        try:
            url = "https://oapi.dingtalk.com/topapi/v2/user/getbymobile"
            token = self.access_token
            params = {"access_token": token}
            body = {"mobile": mobile}
            response = requests.post(url, params=params, json=body, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                logger.info(f"根据手机号{mobile}获取用户信息成功: {mobile}")
                return data.get("result", {})
            else:
                logger.warning(
                    f"根据手机号{mobile}获取用户信息失败: {data.get('errmsg')}"
                )
                return data
        except Exception as e:
            logger.error(f"根据手机号{mobile}获取用户信息异常: {str(e)}")
            return {"errcode": -1, "errmsg": str(e)}

    def get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户详细信息

        Args:
            access_token: 访问令牌
            user_id: 用户ID
            https://open.dingtalk.com/document/orgapp/query-user-details
        Returns:
            用户信息字典，失败返回None
        """
        try:
            url = "https://oapi.dingtalk.com/topapi/v2/user/get"
            params = {"access_token": self.access_token}
            data = {"userid": user_id}

            response = requests.post(url, params=params, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("errcode") == 0:
                user_info = result.get("result", {})
                logger.info(f"根据用户ID{user_id}获取用户详细信息成功: {user_info}")
                return user_info
            else:
                logger.error(
                    f"根据用户ID{user_id}获取用户详细信息失败: {result.get('errmsg')}"
                )
                return None

        except Exception as e:
            logger.error(f"根据用户ID{user_id}获取用户详细信息异常: {str(e)}")  
            return None

    def get_user_by_name(self, name: str):
        """
        根据用户名获取用户ID
        """
        try:
            url = "https://api.dingtalk.com/v1.0/contact/users/search"
            headers = {
                "x-acs-dingtalk-access-token": self.access_token,
                "Content-Type": "application/json",
            }
            data = {"queryWord": name, "offset": 0, "size": 100, "fullMatchField": 1}
            response = requests.post(url, headers=headers, json=data, timeout=30)
            # response.raise_for_status()
            # {
            # "hasMore" : false,
            # "totalCount" : 2,
            # "list" : [ "220141953" ]
            # }
            result = response.json()
            if result.get("errcode", 0) == 0 and result.get("totalCount", 0) > 0:
                return result.get("list", [])
            else:
                logger.error(f"根据用户名获取用户ID失败: {result.get('errmsg')}")
                return None
        except Exception as e:
            logger.error(f"根据用户名获取用户ID异常: {str(e)}")
            return None


class DepartmentClient(DingTalkClient):
    """
    部门管理客户端
    """

    def get_dept_by_name(self, queryWord: str):
        """
        根据部门名称获取部门ID
        """
        try:
            url = "https://api.dingtalk.com/v1.0/contact/departments/search"
            headers = {
                "x-acs-dingtalk-access-token": self.access_token,
                "Content-Type": "application/json",
            }
            data = {
                "queryWord": queryWord,
                "offset": 0,
                "size": 100,
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            # response.raise_for_status()
            result = response.json()
            if result.get("totalCount", 0) > 0:
                return result.get("list", [])
            else:
                logger.error(f"根据部门名称获取部门ID失败: {result.get('message')}")
                return None

        except Exception as e:
            logger.error(f"根据部门名称获取部门ID异常: {str(e)}")
            return None

    def get_dept_detail(self, dept_id: int):
        """
        获取部门详细信息
        """
        try:
            url = "https://oapi.dingtalk.com/topapi/v2/department/get"
            params = {"access_token": self.access_token}
            data = {"dept_id": dept_id}
            response = requests.post(url, params=params, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("result", {})
            else:
                logger.error(f"获取部门详细信息失败: {result.get('errmsg')}")
                return None
        except Exception as e:
            logger.error(f"获取部门详细信息异常: {str(e)}")
            return None

    def get_dept_userid(self, dept_id: int):
        """
        根据部门ID获取用户ID列表
        """
        try:
            url = "https://oapi.dingtalk.com/topapi/user/listid"
            params = {"access_token": self.access_token}
            data = {"dept_id": dept_id}
            response = requests.post(url, params=params, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("result", [])
            else:
                logger.error(f"根据部门ID获取用户ID列表失败: {result.get('errmsg')}")
                return None
        except Exception as e:
            logger.error(f"根据部门ID获取用户ID列表异常: {str(e)}")
            return None

    def get_dept_list(self, dept_id: int = None):
        """调用本接口，获取下一级部门基础信息。
        https://open.dingtalk.com/document/orgapp/obtain-the-department-list-v2
        """
        try:
            url = "https://oapi.dingtalk.com/topapi/v2/department/listsub"
            params = {"access_token": self.access_token}
            data = {}
            if dept_id:
                data = {"dept_id": dept_id}
            response = requests.post(url, params=params, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("result", [])
            else:
                logger.error(f"获取部门详细信息失败: {result.get('errmsg')}")
                return None
        except Exception as e:
            logger.error(f"获取部门详细信息异常: {str(e)}")
            return None


class BotClient(DingTalkClient):
    """
    机器人管理客户端
    """

    def send_bot_message(
        self,
        content,
        userids: list = None,
        msg_type: str = "sampleMarkdown",
    ):
        """
        发送机器人消息

        Args:
            content: 消息内容
            userids: 用户ID列表（用于新版API）
            webhook_url: 机器人webhook地址（用于webhook方式）
            msg_type: 消息类型，支持text、markdown、link等
            at_mobiles: @指定手机号列表
            at_all: 是否@所有人

        Returns:
            发送结果
        """
        try:
            # 否则使用原有的API方式
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            headers = {
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": self.access_token,
            }
            body = {
                "robotCode": self.key,
                "userIds": userids,
                "msgKey": msg_type,
                "msgParam": json.dumps(content),
            }
            response = requests.post(url, headers=headers, json=body, timeout=30)
            # response.raise_for_status()
            data = response.json()

            if data.get("processQueryKey"):
                logger.info(f"机器人消息发送成功: {data}")
                return data.get("processQueryKey", data)
            else:
                logger.error(f"机器人消息发送失败: {data}")

                return data

        except Exception as e:
            logger.error(f"发送机器人消息异常: {str(e)}")
            return {"errcode": -1, "errmsg": str(e)}

    def send_group_message_by_webhook(
        self,
        webhook: str,
        secret: Optional[str],
        content: Dict[str, Any],
        msg_type: str = "markdown",
    ) -> Dict[str, Any]:
        """
        通过钉钉机器人 webhook 发送群消息

        参数:
            webhook(str): 机器人webhook地址
            secret(str|None): 机器人密钥(若开启加签则必填)
            content(dict): 消息内容，遵循钉钉webhook消息体格式
            msg_type(str): 消息类型，默认' markdown '

        返回:
            dict: 钉钉返回的响应数据
        """
        try:
            import hmac
            import hashlib
            import base64
            import time as _time
            from urllib.parse import urlencode

            payload: Dict[str, Any] = {"msgtype": msg_type}

            # 根据消息类型封装消息体
            # 兼容传入已是完整消息体的情况
            if msg_type == "text" and "text" in content:
                payload["text"] = content["text"]
            elif msg_type == "markdown" and "markdown" in content:
                payload["markdown"] = content["markdown"]
            else:
                # 假定传入的是markdown简易结构 {title, text}
                if msg_type == "markdown":
                    payload["markdown"] = {
                        "title": content.get("title", "消息通知"),
                        "text": content.get("text", ""),
                    }
                elif msg_type == "text":
                    payload["text"] = {"content": content.get("content", "")}
                else:
                    # 其它类型直接合并
                    payload[msg_type] = content

            # 若启用加签，则计算签名并拼接到 webhook
            signed_webhook = webhook
            if secret:
                timestamp = str(int(_time.time() * 1000))
                string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
                sign = base64.b64encode(
                    hmac.new(secret.encode("utf-8"), string_to_sign, digestmod=hashlib.sha256).digest()
                ).decode("utf-8")
                query = urlencode({"timestamp": timestamp, "sign": sign})
                if "?" in signed_webhook:
                    signed_webhook = f"{signed_webhook}&{query}"
                else:
                    signed_webhook = f"{signed_webhook}?{query}"

            response = requests.post(signed_webhook, json=payload, timeout=30)
            data = response.json()

            if isinstance(data, dict) and data.get("errcode") == 0:
                logger.info(f"群消息发送成功: {data}")
                return data
            else:
                logger.error(f"群消息发送失败: {data}")
                return data if isinstance(data, dict) else {"raw": data}

        except Exception as e:
            logger.error(f"群消息发送异常: {str(e)}")
            return {"errcode": -1, "errmsg": str(e)}
