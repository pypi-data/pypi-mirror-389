"""
Django钉钉基础模块测试用例
测试项目的主要功能模块：用户管理、消息发送、信号通知等
"""

from django.test import TestCase
from django.test import Client
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
import json

from .models import UserInfo, Department, BotHook
from .manager import UserManager, DepartmentManager
from .signals import NotificationManager, data_fetched, message_received


class UserManagerTestCase(TestCase):
    """
    用户管理器测试用例
    测试三层架构数据获取逻辑
    """

    def setUp(self):
        """测试前准备工作"""
        self.user_manager = UserManager()
        self.test_user_name = "测试用户"
        self.test_user_mobile = "13800138000"

    @patch('django_rick_base.manager.UserClient')
    def test_get_user_by_name_from_database(self, mock_user_client):
        """测试从数据库获取用户信息"""
        # 创建测试用户
        user = UserInfo.objects.create(
            id="test_user_001",
            name=self.test_user_name,
            mobile=self.test_user_mobile
        )
        
        # 调用方法
        result = self.user_manager.get_user_by_name(self.test_user_name)
        
        # 验证结果
        self.assertEqual(result, user)
        # 确保没有调用API
        mock_user_client.assert_not_called()

    @patch('django_rick_base.manager.UserClient')
    def test_get_user_by_name_from_api(self, mock_user_client):
        """测试从API获取用户信息"""
        # 模拟API返回
        mock_client_instance = mock_user_client.return_value
        mock_client_instance.get_user_by_name.return_value = ["test_user_001"]
        
        # 调用方法
        result = self.user_manager.get_user_by_name(self.test_user_name)
        
        # 验证API调用
        mock_client_instance.get_user_by_name.assert_called_once_with(self.test_user_name)
        # 验证用户被创建
        self.assertTrue(UserInfo.objects.filter(name=self.test_user_name).exists())


class DepartmentManagerTestCase(TestCase):
    """
    部门管理器测试用例
    测试部门数据获取逻辑
    """

    def setUp(self):
        """测试前准备工作"""
        self.dept_manager = DepartmentManager()
        self.test_dept_name = "测试部门"

    @patch('django_rick_base.manager.DepartmentClient')
    def test_get_dept_by_name_from_database(self, mock_dept_client):
        """测试从数据库获取部门信息"""
        # 创建测试部门
        dept = Department.objects.create(
            id="test_dept_001",
            name=self.test_dept_name
        )
        
        # 调用方法
        result = self.dept_manager.get_dept_by_name(self.test_dept_name)
        
        # 验证结果
        self.assertEqual(result, dept)
        # 确保没有调用API
        mock_dept_client.assert_not_called()

    @patch('django_rick_base.manager.DepartmentClient')
    def test_get_dept_by_name_from_api(self, mock_dept_client):
        """测试从API获取部门信息"""
        # 模拟API返回
        mock_client_instance = mock_dept_client.return_value
        mock_client_instance.get_dept_by_name.return_value = ["test_dept_001"]
        
        # 调用方法
        result = self.dept_manager.get_dept_by_name(self.test_dept_name)
        
        # 验证API调用
        mock_client_instance.get_dept_by_name.assert_called_once_with(self.test_dept_name)
        # 验证部门被创建
        self.assertTrue(Department.objects.filter(name=self.test_dept_name).exists())


class MessageAPITestCase(APITestCase):
    """
    消息API测试用例
    测试消息发送接口
    """

    def setUp(self):
        """测试前准备工作"""
        self.client = Client()
        self.single_message_url = reverse('dingtalk-message-user')
        self.group_message_url = reverse('dingtalk-message-group')
        self.health_check_url = reverse('dingtalk-health')

    @patch('django_rick_base.views.DingTalkClient')
    def test_health_check(self, mock_dingtalk_client):
        """测试健康检查接口"""
        # 模拟DingTalkClient
        mock_client_instance = mock_dingtalk_client.return_value
        mock_client_instance.access_token = "test_access_token"
        
        response = self.client.get(self.health_check_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('status', response.data['data'])
        self.assertEqual(response.data['data']['status'], 'ok')

    @patch('django_rick_base.views.BotClient')
    @patch('django_rick_base.views.DingTalkClient')
    def test_single_message_success(self, mock_dingtalk_client, mock_bot_client):
        """测试单条消息发送成功"""
        # 模拟DingTalkClient
        mock_dingtalk_instance = mock_dingtalk_client.return_value
        mock_dingtalk_instance.access_token = "test_access_token"
        
        # 模拟BotClient
        mock_client_instance = mock_bot_client.return_value
        mock_client_instance.send_bot_message.return_value = {
            "errcode": 0,
            "errmsg": "ok"
        }
        
        # 准备测试数据
        data = {
            "query": "13800138000",
            "content": {
                "title": "测试消息",
                "text": "这是一条测试消息"
            }
        }
        
        # 发送请求
        response = self.client.post(
            self.single_message_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)

    def test_single_message_invalid_data(self):
        """测试单条消息发送参数错误"""
        # 准备无效数据
        data = {
            "query": "",  # 空查询参数
            "content": {}
        }
        
        # 发送请求
        response = self.client.post(
            self.single_message_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('django_rick_base.views.BotClient')
    @patch('django_rick_base.views.DingTalkClient')
    def test_group_message_with_hook_name(self, mock_dingtalk_client, mock_bot_client):
        """测试通过钩子名称发送群消息"""
        # 模拟DingTalkClient
        mock_dingtalk_instance = mock_dingtalk_client.return_value
        mock_dingtalk_instance.access_token = "test_access_token"
        
        # 创建测试机器人钩子
        bot_hook = BotHook.objects.create(
            hook_name="test_bot",
            webhook="https://oapi.dingtalk.com/robot/send?access_token=test",
            secret="test_secret"
        )
        
        # 模拟BotClient
        mock_client_instance = mock_bot_client.return_value
        mock_client_instance.send_group_message_by_webhook.return_value = {
            "errcode": 0,
            "errmsg": "ok"
        }
        
        # 准备测试数据
        data = {
            "hook_name": "test_bot",
            "content": {
                "msgtype": "markdown",
                "markdown": {
                    "title": "测试群消息",
                    "text": "这是一条测试群消息"
                }
            }
        }
        
        # 发送请求
        response = self.client.post(
            self.group_message_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)


class SignalTestCase(TestCase):
    """
    信号机制测试用例
    测试自定义信号发送和接收
    """

    def setUp(self):
        """测试前准备工作"""
        self.received_signals = []

    def signal_receiver(self, sender, **kwargs):
        """信号接收器"""
        self.received_signals.append({
            'sender': sender,
            'kwargs': kwargs
        })

    def test_data_fetched_signal(self):
        """测试数据获取完成信号"""
        # 注册信号接收器
        data_fetched.connect(self.signal_receiver)
        
        # 发送信号
        test_data = {"user_id": "test_001", "name": "测试用户"}
        NotificationManager.send_data_fetched_notification(
            sender=self.__class__,
            data_type="user",
            data=test_data
        )
        
        # 验证信号接收
        self.assertEqual(len(self.received_signals), 1)
        signal_data = self.received_signals[0]
        self.assertEqual(signal_data['sender'], self.__class__)
        self.assertEqual(signal_data['kwargs']['data_type'], "user")
        self.assertEqual(signal_data['kwargs']['data'], test_data)
        
        # 断开信号连接
        data_fetched.disconnect(self.signal_receiver)

    def test_message_received_signal(self):
        """测试消息接收信号"""
        # 注册信号接收器
        message_received.connect(self.signal_receiver)
        
        # 发送信号
        test_message = {"type": "text", "content": "测试消息"}
        NotificationManager.send_message_received_notification(
            sender=self.__class__,
            message_type="callback",
            message=test_message
        )
        
        # 验证信号接收
        self.assertEqual(len(self.received_signals), 1)
        signal_data = self.received_signals[0]
        self.assertEqual(signal_data['sender'], self.__class__)
        self.assertEqual(signal_data['kwargs']['message_type'], "callback")
        self.assertEqual(signal_data['kwargs']['message'], test_message)
        
        # 断开信号连接
        message_received.disconnect(self.signal_receiver)


class ModelTestCase(TestCase):
    """
    数据模型测试用例
    测试模型创建和基本操作
    """

    def test_user_info_creation(self):
        """测试用户信息模型创建"""
        user = UserInfo.objects.create(
            id="test_user_001",
            name="测试用户",
            mobile="13800138000",
            email="test@example.com"
        )
        
        self.assertEqual(user.name, "测试用户")
        self.assertEqual(user.mobile, "13800138000")
        self.assertTrue(user.create_time is not None)
        self.assertTrue(user.update_time is not None)

    def test_department_creation(self):
        """测试部门模型创建"""
        dept = Department.objects.create(
            id="test_dept_001",
            name="测试部门",
            parent_id="0",
            order=1
        )
        
        self.assertEqual(dept.name, "测试部门")
        self.assertEqual(dept.parent_id, "0")
        self.assertEqual(dept.order, 1)

    def test_bot_hook_creation(self):
        """测试机器人钩子模型创建"""
        bot_hook = BotHook.objects.create(
            hook_name="test_bot",
            webhook="https://oapi.dingtalk.com/robot/send?access_token=test",
            secret="test_secret"
        )
        
        self.assertEqual(bot_hook.hook_name, "test_bot")
        self.assertIn("access_token=test", bot_hook.webhook)
        self.assertEqual(bot_hook.secret, "test_secret")
