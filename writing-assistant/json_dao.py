"""\nJSON数据访问层 (DAO - Data Access Object)\n使用JSON文件存储替代数据库操作\n"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from json_storage import UserStorage, ProjectStorage, ConfigStorage
from auth_utils import hash_password, verify_password, validate_password_strength

class UserDAO:
    """用户数据访问对象 - JSON版本"""
    
    def __init__(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def create_user(self, username: str, password: str, grade: str, subject: str = '语文') -> Dict:
        """创建用户"""
        # 验证密码强度
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            raise ValueError(message)
        
        # 加密密码
        password_hash, _ = hash_password(password)
        
        return UserStorage.create_user(
            username=username,
            password_hash=password_hash,
            grade=grade,
            subject=subject
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        return UserStorage.get_user_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        return UserStorage.get_user_by_username(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """验证用户登录"""
        user = self.get_user_by_username(username)
        if user and verify_password(password, user['password_hash']):
            return user
        return None
    
    def get_all_users(self) -> List[Dict]:
        """获取所有用户"""
        return UserStorage.get_all_users()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[Dict]:
        """更新用户信息"""
        return UserStorage.update_user(user_id, **kwargs)
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        return UserStorage.delete_user(user_id)

class ProjectDAO:
    """写作项目数据访问对象 - JSON版本"""
    
    def __init__(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def create_project(self, user_id: int, title: str, topic: str, article_type: str, subject: str, grade: str = '初中') -> Dict:
        """创建写作项目"""
        return ProjectStorage.create_project(
            user_id=user_id,
            title=title,
            topic=topic,
            article_type=article_type,
            subject=subject,
            grade=grade
        )
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """根据ID获取项目"""
        return ProjectStorage.get_project_by_id(project_id)
    
    def get_projects_by_user(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """获取用户的项目"""
        return ProjectStorage.get_projects_by_user(user_id, status)
    
    def update_project_content(self, project_id: int, content_type: str, content: str) -> Optional[Dict]:
        """更新项目内容"""
        valid_types = ['brainstorm_content', 'outline_content', 'writing_content']
        if content_type not in valid_types:
            raise ValueError(f"无效的内容类型: {content_type}")
        
        # 计算字数（仅对正文内容）
        update_data = {content_type: content}
        if content_type == 'writing_content':
            update_data['word_count'] = len(content.replace(' ', '').replace('\n', ''))
        
        return ProjectStorage.update_project(project_id, **update_data)
    
    def update_project_status(self, project_id: int, status: str) -> Optional[Dict]:
        """更新项目状态"""
        valid_statuses = ['draft', 'writing', 'completed']
        if status not in valid_statuses:
            raise ValueError(f"无效的状态: {status}")
        
        update_data = {'status': status}
        if status == 'completed':
            update_data['completed_at'] = datetime.now().isoformat()
        
        return ProjectStorage.update_project(project_id, **update_data)
    
    def save_ai_feedback(self, project_id: int, feedback: Dict[str, Any]) -> Optional[Dict]:
        """保存AI反馈"""
        feedback_json = json.dumps(feedback, ensure_ascii=False)
        return ProjectStorage.update_project(project_id, ai_feedback=feedback_json)
    
    def save_scores(self, project_id: int, overall_score: int, dimension_scores: Dict[str, int]) -> Optional[Dict]:
        """保存评分"""
        scores_json = json.dumps(dimension_scores, ensure_ascii=False)
        return ProjectStorage.update_project(
            project_id,
            final_score=overall_score,
            scores=scores_json
        )
    
    def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        return ProjectStorage.delete_project(project_id)
    
    def get_recent_projects(self, limit: int = 10) -> List[Dict]:
        """获取最近的项目"""
        return ProjectStorage.get_recent_projects(limit)

class ConfigDAO:
    """系统配置数据访问对象 - JSON版本"""
    
    def __init__(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def get_config(self, key: str) -> Optional[Dict]:
        """获取配置"""
        config_data = ConfigStorage.get_config(key)
        if config_data:
            return {
                'key': key,
                'value': config_data.get('value'),
                'description': config_data.get('description', ''),
                'updated_at': config_data.get('updated_at')
            }
        return None
    
    def set_config(self, key: str, value: str, description: str = '') -> Dict:
        """设置配置"""
        ConfigStorage.set_config(key, value, description)
        return {
            'key': key,
            'value': value,
            'description': description,
            'updated_at': datetime.now().isoformat()
        }
    
    def get_all_configs(self) -> List[Dict]:
        """获取所有配置"""
        all_configs = ConfigStorage.get_all_configs()
        result = []
        for key, config_data in all_configs.items():
            result.append({
                'key': key,
                'value': config_data.get('value'),
                'description': config_data.get('description', ''),
                'updated_at': config_data.get('updated_at')
            })
        return result

# 装饰器函数，用于兼容原有代码
def with_user_dao(func):
    """用户DAO装饰器"""
    def wrapper(*args, **kwargs):
        with UserDAO() as dao:
            return func(dao, *args, **kwargs)
    return wrapper

def with_project_dao(func):
    """项目DAO装饰器"""
    def wrapper(*args, **kwargs):
        with ProjectDAO() as dao:
            return func(dao, *args, **kwargs)
    return wrapper

def with_config_dao(func):
    """配置DAO装饰器"""
    def wrapper(*args, **kwargs):
        with ConfigDAO() as dao:
            return func(dao, *args, **kwargs)
    return wrapper

# 为了兼容性，创建类似原DAO的对象结构
class MockUser:
    """模拟User对象，用于兼容性"""
    def __init__(self, data: Dict):
        for key, value in data.items():
            setattr(self, key, value)
    
    def to_dict(self):
        return {key: value for key, value in self.__dict__.items()}

class MockProject:
    """模拟WritingProject对象，用于兼容性"""
    def __init__(self, data: Dict):
        for key, value in data.items():
            setattr(self, key, value)
    
    def to_dict(self):
        return {key: value for key, value in self.__dict__.items()}

# 兼容性函数，将字典转换为对象
def dict_to_user(data: Dict) -> MockUser:
    """将字典转换为User对象"""
    return MockUser(data) if data else None

def dict_to_project(data: Dict) -> MockProject:
    """将字典转换为Project对象"""
    return MockProject(data) if data else None

def dicts_to_users(data_list: List[Dict]) -> List[MockUser]:
    """将字典列表转换为User对象列表"""
    return [MockUser(data) for data in data_list]

def dicts_to_projects(data_list: List[Dict]) -> List[MockProject]:
    """将字典列表转换为Project对象列表"""
    return [MockProject(data) for data in data_list]