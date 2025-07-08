"""
AI智能写作辅导软件主应用
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import logging
import json
from datetime import datetime
from markupsafe import Markup

from config import get_config
from json_storage import init_default_data
from routes.main import main_bp
from routes.api import api_bp
from performance import PerformanceMiddleware

# 获取配置
config = get_config()

def create_app():
    """应用工厂函数"""
    # 创建Flask应用
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    
    # 启用CORS
    CORS(app)
    
    # 添加自定义过滤器
    @app.template_filter('from_json')
    def from_json_filter(value):
        """JSON字符串转换为Python对象"""
        if not value:
            return {}
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @app.template_filter('nl2br')
    def nl2br_filter(value):
        """换行符转换为HTML的<br>标签"""
        if not value:
            return ''
        return Markup(value.replace('\n', '<br>'))
    
    # 添加模板上下文处理器
    @app.context_processor
    def inject_template_vars():
        """注入模板全局变量"""
        return {
            'current_year': datetime.now().year,
            'build_date': '2025-07-06',
            'app_version': 'v2.0.0'
        }
    
    # 配置日志
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # 初始化性能监控
    PerformanceMiddleware(app)
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return render_template('error.html', 
                             error_code=404,
                             error_message='页面未找到'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logger.error(f"内部服务器错误: {error}")
        return render_template('error.html',
                             error_code=500,
                             error_message='内部服务器错误'), 500
    
    # 初始化JSON存储
    try:
        init_default_data()
        logger.info("JSON存储初始化成功")
    except Exception as e:
        logger.error(f"JSON存储初始化失败: {e}")
    
    logger.info("AI智能写作辅导软件启动成功")
    return app

if __name__ == '__main__':
    # 创建应用
    app = create_app()
    
    # 启动应用
    print(f"启动AI智能写作辅导软件")
    print(f"访问地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    
    app.run(
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        debug=config.DEBUG
    )