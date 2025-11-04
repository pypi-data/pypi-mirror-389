"""
用户/部门 管理类,整合client,保证数据一致性
实现三层架构：优先从数据库获取数据，不存在则从API获取并保存
"""

from django.db.models import Manager
import logging
from .client import UserClient, DepartmentClient
from .models import UserInfo, Department
from .signals import NotificationManager

logger = logging.getLogger(__name__)


class UserManager(Manager):
    """
    用户管理器
    实现三层架构：优先从数据库获取，不存在则从API获取并保存
    """

    def get_user_by_name(self, name: str):
        """
        根据用户名获取用户信息
        优先从数据库获取，不存在则从API获取并保存
        
        参数:
            name: 用户名
            
        返回:
            UserInfo对象或None
        """
        try:
            # 1. 优先从数据库获取
            user_info = UserInfo.objects.filter(name=name).first()
            if user_info:
                logger.info(f"从数据库获取用户信息: {name}")
                return user_info
            
            # 2. 数据库不存在，从API获取
            logger.info(f"数据库不存在用户 {name}，从API获取")
            user_client = UserClient()
            userids = user_client.get_user_by_name(name)
            
            if not userids:
                logger.warning(f"API未找到用户: {name}")
                return None
            
            # 3. 保存到数据库
            for user_id in userids:
                user_info = UserInfo.objects.create(
                    name=name,
                    id=user_id,
                )
                user_info.save()
                logger.info(f"用户信息保存到数据库: {name} -> {user_id}")
            
            # 4. 发送数据获取完成通知
            NotificationManager.send_data_fetched_notification(
                sender=self.__class__,
                data_type="user_info",
                data={"name": name, "userids": userids}
            )
            
            # 5. 返回数据库中的用户信息
            return UserInfo.objects.filter(name=name).first()
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {name}, 错误: {e}")
            return None


class DepartmentManager(Manager):
    """
    部门管理器
    实现三层架构：优先从数据库获取，不存在则从API获取并保存
    """

    def get_dept_by_name(self, queryWord: str):
        """
        根据部门名称获取部门信息
        优先从数据库获取，不存在则从API获取并保存
        
        参数:
            queryWord: 部门名称
            
        返回:
            Department对象或None
        """
        try:
            # 1. 优先从数据库获取
            dept_info = Department.objects.filter(name=queryWord).first()
            if dept_info:
                logger.info(f"从数据库获取部门信息: {queryWord}")
                return dept_info
            
            # 2. 数据库不存在，从API获取
            logger.info(f"数据库不存在部门 {queryWord}，从API获取")
            dept_client = DepartmentClient()
            dept_data = dept_client.get_dept_by_name(queryWord)
            
            if not dept_data:
                logger.warning(f"API未找到部门: {queryWord}")
                return None
            
            # 3. 保存到数据库
            dept_info = Department.objects.create(
                id=dept_data.get('id'),
                name=dept_data.get('name'),
                parent_id=dept_data.get('parentid'),
                order=dept_data.get('order'),
                extra=dept_data
            )
            dept_info.save()
            logger.info(f"部门信息保存到数据库: {queryWord} -> {dept_data.get('id')}")
            
            # 4. 发送数据获取完成通知
            NotificationManager.send_data_fetched_notification(
                sender=self.__class__,
                data_type="department_info",
                data=dept_data
            )
            
            # 5. 返回数据库中的部门信息
            return Department.objects.filter(name=queryWord).first()
            
        except Exception as e:
            logger.error(f"获取部门信息失败: {queryWord}, 错误: {e}")
            return None
