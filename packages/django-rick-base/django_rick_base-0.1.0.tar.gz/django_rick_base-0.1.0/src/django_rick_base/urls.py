#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册视图集
# router.register(r'userinfo', views.UserInfoViewSet, basename='dingtalk-userinfo')

# URL配置
system_url = [
    # 包含路由器生成的URL
    # path('', include(router.urls)),
    
    # 消息发送接口(兼容旧路径)
    path('message/send/', views.DingTalkMessageView.as_view(), name='dingtalk-message-send'),

    # 单独消息发送接口
    path('message/user/', views.DingTalkSingleMessageView.as_view(), name='dingtalk-message-user'),

    # 群消息发送接口
    path('message/group/', views.DingTalkGroupMessageView.as_view(), name='dingtalk-message-group'),
    
    # 钉钉回调接口
    path('callback/', views.callback, name='dingtalk-callback'),
    
    # 健康检查接口
    path('health/', views.health_check, name='dingtalk-health'),
]

urlpatterns = system_url
