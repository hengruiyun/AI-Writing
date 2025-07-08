"""\nJSON文件存储模块\n替代数据库存储，使用JSON文件保存数据\n"""
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# 数据存储目录
DATA_DIR = Path('data')
USERS_FILE = DATA_DIR / 'users.json'
PROJECTS_FILE = DATA_DIR / 'projects.json'
CONFIG_FILE = DATA_DIR / 'config.json'

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

@dataclass
class User:
    """用户数据类"""
    id: int
    username: str
    password_hash: str
    grade: str = '初中'
    subject: str = '语文'
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class WritingProject:
    """写作项目数据类"""
    id: int
    user_id: int
    title: str
    topic: str
    article_type: str
    subject: str
    grade: str = '初中'  # 添加年级字段
    brainstorm_content: str = ''
    outline_content: str = ''
    writing_content: str = ''
    ai_feedback: str = ''
    final_score: int = 0
    scores: str = ''
    status: str = 'draft'
    word_count: int = 0
    created_at: str = None
    updated_at: str = None
    completed_at: str = None
    
    def __post_init__(self):
        now = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    def to_dict(self):
        return asdict(self)

class JSONStorage:
    """JSON文件存储管理器"""
    
    @staticmethod
    def _load_json(file_path: Path, default=None):
        """加载JSON文件"""
        if default is None:
            default = []
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    
    @staticmethod
    def _save_json(file_path: Path, data):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    @staticmethod
    def _get_next_id(items: List[Dict]) -> int:
        """获取下一个ID"""
        if not items:
            return 1
        return max(item.get('id', 0) for item in items) + 1

class UserStorage(JSONStorage):
    """用户存储管理"""
    
    @classmethod
    def get_all_users(cls) -> List[Dict]:
        """获取所有用户"""
        return cls._load_json(USERS_FILE)
    
    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        users = cls.get_all_users()
        for user in users:
            if user.get('id') == user_id:
                return user
        return None
    
    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        users = cls.get_all_users()
        for user in users:
            if user.get('username') == username:
                return user
        return None
    
    @classmethod
    def create_user(cls, username: str, password_hash: str, grade: str = '初中', subject: str = '语文') -> Dict:
        """创建用户"""
        users = cls.get_all_users()
        
        # 检查用户名是否已存在
        if cls.get_user_by_username(username):
            raise ValueError(f"用户名 '{username}' 已存在")
        
        user_id = cls._get_next_id(users)
        user = User(
            id=user_id,
            username=username,
            password_hash=password_hash,
            grade=grade,
            subject=subject
        )
        
        users.append(user.to_dict())
        cls._save_json(USERS_FILE, users)
        return user.to_dict()
    
    @classmethod
    def update_user(cls, user_id: int, **kwargs) -> Optional[Dict]:
        """更新用户信息"""
        users = cls.get_all_users()
        
        for i, user in enumerate(users):
            if user.get('id') == user_id:
                for key, value in kwargs.items():
                    if key in user:
                        user[key] = value
                cls._save_json(USERS_FILE, users)
                return user
        return None
    
    @classmethod
    def delete_user(cls, user_id: int) -> bool:
        """删除用户"""
        users = cls.get_all_users()
        
        for i, user in enumerate(users):
            if user.get('id') == user_id:
                users.pop(i)
                cls._save_json(USERS_FILE, users)
                return True
        return False

class ProjectStorage(JSONStorage):
    """项目存储管理"""
    
    @classmethod
    def get_all_projects(cls) -> List[Dict]:
        """获取所有项目"""
        return cls._load_json(PROJECTS_FILE)
    
    @classmethod
    def get_project_by_id(cls, project_id: int) -> Optional[Dict]:
        """根据ID获取项目"""
        projects = cls.get_all_projects()
        for project in projects:
            if project.get('id') == project_id:
                return project
        return None
    
    @classmethod
    def get_projects_by_user(cls, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """获取用户的项目"""
        projects = cls.get_all_projects()
        user_projects = [p for p in projects if p.get('user_id') == user_id]
        
        if status:
            user_projects = [p for p in user_projects if p.get('status') == status]
        
        # 按创建时间倒序排列
        user_projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return user_projects
    
    @classmethod
    def create_project(cls, user_id: int, title: str, topic: str, article_type: str, subject: str, grade: str = '初中') -> Dict:
        """创建项目"""
        projects = cls.get_all_projects()
        
        project_id = cls._get_next_id(projects)
        project = WritingProject(
            id=project_id,
            user_id=user_id,
            title=title,
            topic=topic,
            article_type=article_type,
            subject=subject,
            grade=grade
        )
        
        projects.append(project.to_dict())
        cls._save_json(PROJECTS_FILE, projects)
        return project.to_dict()
    
    @classmethod
    def update_project(cls, project_id: int, **kwargs) -> Optional[Dict]:
        """更新项目"""
        projects = cls.get_all_projects()
        
        for i, project in enumerate(projects):
            if project.get('id') == project_id:
                for key, value in kwargs.items():
                    if key in project:
                        project[key] = value
                project['updated_at'] = datetime.now().isoformat()
                cls._save_json(PROJECTS_FILE, projects)
                return project
        return None
    
    @classmethod
    def delete_project(cls, project_id: int) -> bool:
        """删除项目"""
        projects = cls.get_all_projects()
        
        for i, project in enumerate(projects):
            if project.get('id') == project_id:
                projects.pop(i)
                cls._save_json(PROJECTS_FILE, projects)
                return True
        return False
    
    @classmethod
    def get_recent_projects(cls, limit: int = 10) -> List[Dict]:
        """获取最近的项目"""
        projects = cls.get_all_projects()
        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return projects[:limit]

class ConfigStorage(JSONStorage):
    """配置存储管理"""
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return cls._load_json(CONFIG_FILE, {})
    
    @classmethod
    def get_config(cls, key: str, default=None):
        """获取配置值"""
        configs = cls.get_all_configs()
        return configs.get(key, default)
    
    @classmethod
    def set_config(cls, key: str, value: Any, description: str = '') -> bool:
        """设置配置值"""
        configs = cls.get_all_configs()
        configs[key] = {
            'value': value,
            'description': description,
            'updated_at': datetime.now().isoformat()
        }
        return cls._save_json(CONFIG_FILE, configs)
    
    @classmethod
    def delete_config(cls, key: str) -> bool:
        """删除配置"""
        configs = cls.get_all_configs()
        if key in configs:
            del configs[key]
            cls._save_json(CONFIG_FILE, configs)
            return True
        return False

def init_default_data():
    """初始化默认数据"""
    # 创建默认用户
    try:
        from auth_utils import hash_password
        password_hash, _ = hash_password('default123')
        UserStorage.create_user(
            username='267278466@qq.com',
            password_hash=password_hash,
            grade='初中',
            subject='语文'
        )
        print("默认用户创建成功")
    except ValueError:
        print("默认用户已存在")
    
    # 创建默认配置
    default_configs = {
        'ai_model': 'gpt-3.5-turbo',
        'max_word_count': 800,
        'enable_ai_suggestions': True,
        'auto_save_interval': 30
    }
    
    for key, value in default_configs.items():
        if ConfigStorage.get_config(key) is None:
            ConfigStorage.set_config(key, value, f"默认配置: {key}")
    
    print("默认配置初始化完成")

if __name__ == '__main__':
    init_default_data()