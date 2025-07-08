"""
数据库初始化脚本
"""
import os
from models import Base, engine, SessionLocal, User, WritingProject, SystemConfig
from config import get_config

config = get_config()

# 防止重复初始化的标志
_db_initialized = False

def init_db():
    """初始化数据库"""
    global _db_initialized
    
    if _db_initialized:
        return
        
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        # 创建默认配置
        create_default_config()
        
        # 创建默认用户
        create_default_user()
        
        _db_initialized = True
        print("数据库初始化成功")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise

def create_default_config():
    """创建默认系统配置"""
    session = SessionLocal()
    try:
        # 检查是否已有配置
        existing_config = session.query(SystemConfig).first()
        if existing_config:
            return
        
        # 创建默认配置
        default_configs = [
            {
                'key': 'system_initialized',
                'value': 'true',
                'description': '系统是否已初始化'
            },
            {
                'key': 'default_grade',
                'value': '初中',
                'description': '默认年级'
            },
            {
                'key': 'default_subject',
                'value': '语文',
                'description': '默认学科'
            },
            {
                'key': 'auto_save_enabled',
                'value': 'true',
                'description': '是否启用自动保存'
            }
        ]
        
        for config_data in default_configs:
            # 检查每个配置是否已存在，避免重复插入
            existing = session.query(SystemConfig).filter_by(key=config_data['key']).first()
            if not existing:
                config_obj = SystemConfig(**config_data)
                session.add(config_obj)
        
        session.commit()
        print("默认配置创建成功")
        
    except Exception as e:
        session.rollback()
        print(f"创建默认配置失败: {e}")
        raise
    finally:
        session.close()

def create_default_user():
    """创建默认用户"""
    session = SessionLocal()
    try:
        # 检查是否已有用户
        existing_user = session.query(User).filter_by(username='267278466@qq.com').first()
        if existing_user:
            return
        
        # 创建默认用户
        from auth_utils import hash_password
        password_hash, _ = hash_password('default123')  # 获取密码哈希字符串
        default_user = User(
            username='267278466@qq.com',
            password_hash=password_hash,
            grade='初中',
            subject='语文'
        )
        
        session.add(default_user)
        session.commit()
        print("默认用户创建成功")
        
    except Exception as e:
        session.rollback()
        print(f"创建默认用户失败: {e}")
        raise
    finally:
        session.close()

def reset_db():
    """重置数据库"""
    global _db_initialized
    
    try:
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        
        # 重置初始化标志
        _db_initialized = False
        
        # 重新创建
        init_db()
        
        print("数据库重置成功")
        
    except Exception as e:
        print(f"数据库重置失败: {e}")
        raise

if __name__ == '__main__':
    init_db()