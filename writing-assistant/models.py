"""
数据库模型
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import get_config

config = get_config()

# 创建数据库引擎
# 只在DEBUG模式且LOG_LEVEL为DEBUG时输出SQL日志
echo_sql = config.DEBUG and getattr(config, 'LOG_LEVEL', 'INFO') == 'DEBUG'
engine = create_engine(config.DATABASE_URL, echo=echo_sql)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)  # 加密密码
    grade = Column(String(20), nullable=True, default='初中')  # 小学/初中/高中
    subject = Column(String(20), nullable=True, default='语文')  # 语文/英语
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    projects = relationship("WritingProject", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', grade='{self.grade}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'grade': self.grade,
            'subject': self.subject,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WritingProject(Base):
    """写作项目模型"""
    __tablename__ = 'writing_projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    topic = Column(Text, nullable=False)  # 写作题目
    article_type = Column(String(30), nullable=False)  # 文章类型
    subject = Column(String(20), nullable=False)
    
    # 写作内容
    brainstorm_content = Column(Text)  # 构思内容
    outline_content = Column(Text)  # 提纲内容
    writing_content = Column(Text)  # 正文内容
    
    # AI反馈（JSON格式）
    ai_feedback = Column(Text)  # AI建议和反馈
    
    # 评分信息
    final_score = Column(Integer, default=0)  # 总分
    scores = Column(Text)  # 各维度得分（JSON）
    
    # 状态信息
    status = Column(String(20), default='draft')  # draft/writing/completed
    word_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="projects")
    
    def __repr__(self):
        return f"<WritingProject(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'topic': self.topic,
            'article_type': self.article_type,
            'subject': self.subject,
            'brainstorm_content': self.brainstorm_content,
            'outline_content': self.outline_content,
            'writing_content': self.writing_content,
            'ai_feedback': self.ai_feedback,
            'final_score': self.final_score,
            'scores': self.scores,
            'status': self.status,
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class SystemConfig(Base):
    """系统配置模型"""
    __tablename__ = 'system_config'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 