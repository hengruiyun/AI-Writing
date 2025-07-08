"""
API路由模块
处理用户和项目的CRUD操作，统一AI上下文传递
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import json

from json_dao import UserDAO, ProjectDAO, with_user_dao, with_project_dao, dict_to_user, dict_to_project, dicts_to_projects
from ai_service import sync_generate_topic, sync_analyze_content, sync_evaluate_article, sync_health_check, sync_test_connection, sync_generate_suggestions, sync_generate_stage_suggestions
from scoring_service import ScoringService
from ai_service import AIService

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

def success_response(data=None, message="操作成功"):
    """成功响应"""
    return jsonify({
        'success': True,
        'data': data,
        'message': message
    })

def error_response(message="操作失败", code=400):
    """错误响应"""
    return jsonify({
        'success': False,
        'message': message
    }), code

def get_user_ai_settings(user_id: int) -> dict:
    """从用户配置中读取AI设置"""
    from json_storage import UserStorage
    
    user = UserStorage.get_user_by_id(user_id)
    if not user:
        return {
            'provider': 'Ollama',  # 默认使用Ollama
            'model': 'gemma3:latest',
            'api_key': '',
            'base_url': 'localhost:11434'
        }
    
    # 如果用户没有设置AI配置，使用默认值
    provider = user.get('ai_provider', 'Ollama')
    model = user.get('ai_model', 'gemma2:latest')
    base_url = user.get('ai_base_url', 'localhost:11434')
    
    return {
        'provider': provider,
        'model': model,
        'api_key': user.get('ai_api_key', ''),
        'base_url': base_url
    }

def build_ai_context(user, project=None, extra_context=None) -> dict:
    """构建AI上下文信息"""
    context = {
        'grade': user.get('grade', '') if user else '',
        'subject': user.get('subject', '') if user else '',
        'topic': project.get('topic', '') if project else '',
        'article_type': project.get('article_type', '') if project else '',
        'requirement': ''
    }
    
    if extra_context:
        context.update(extra_context)
    
    return context

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        ai_status = sync_health_check()
        return jsonify({
            'status': 'healthy',
            'ai_service': ai_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return error_response(f"健康检查失败: {str(e)}", 500)

# 用户管理API
# 用户注册功能已删除

# 用户登录功能已删除

# 用户登出功能已删除

@api_bp.route('/users/current', methods=['GET'])
def get_current_user():
    """获取当前用户信息"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        @with_user_dao
        def _get_user(dao):
            user = dao.get_user_by_id(user_id)
            return user  # JSON DAO直接返回字典
        
        user_data = _get_user()
        
        if not user_data:
            return error_response("用户不存在", 404)
        
        return success_response(user_data)
        
    except Exception as e:
        return error_response(f"获取用户信息失败: {str(e)}", 500)

@api_bp.route('/users/settings', methods=['PUT'])
def update_user_settings():
    """更新用户设置"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        grade = data.get('grade')
        subject = data.get('subject')
        ai_provider = data.get('ai_provider', '')
        ai_model = data.get('ai_model', '')
        ai_api_key = data.get('ai_api_key', '')
        ai_base_url = data.get('ai_base_url', '')
        
        if not grade or not subject:
            return error_response("年级和学科不能为空")
        
        @with_user_dao
        def _update_user(dao):
            user = dao.update_user(user_id, 
                                 grade=grade, 
                                 subject=subject,
                                 ai_provider=ai_provider,
                                 ai_model=ai_model,
                                 ai_api_key=ai_api_key,
                                 ai_base_url=ai_base_url)
            return user  # JSON DAO直接返回字典
        
        user_data = _update_user()
        
        if not user_data:
            return error_response("用户不存在", 404)
        
        return success_response(user_data, "设置更新成功")
        
    except Exception as e:
        return error_response(f"更新设置失败: {str(e)}", 500)

@api_bp.route('/users/ai-settings', methods=['PUT'])
def update_user_ai_settings():
    """更新用户AI设置"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        ai_provider = data.get('ai_provider', '')
        ai_model = data.get('ai_model', '')
        ai_api_key = data.get('ai_api_key', '')
        ai_base_url = data.get('ai_base_url', '')
        
        @with_user_dao
        def _update_user_ai(dao):
            user = dao.get_user_by_id(user_id)
            if not user:
                return None
            
            # 保存更新 - 直接传递字段而不是整个user对象
            updated_user = dao.update_user(user_id, 
                ai_provider=ai_provider,
                ai_model=ai_model,
                ai_api_key=ai_api_key,
                ai_base_url=ai_base_url
            )
            return updated_user
        
        updated_user = _update_user_ai()
        if not updated_user:
            return error_response("用户不存在", 404)
        
        return success_response({
            'ai_provider': updated_user.get('ai_provider', ''),
            'ai_model': updated_user.get('ai_model', ''),
            'ai_base_url': updated_user.get('ai_base_url', '')
        }, "AI设置更新成功")
        
    except Exception as e:
        return error_response(f"更新AI设置失败: {str(e)}", 500)

@api_bp.route('/users/ai-settings', methods=['GET'])
def get_user_ai_settings_api():
    """获取用户AI设置"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        ai_settings = get_user_ai_settings(user_id)
        return success_response(ai_settings)
        
    except Exception as e:
        return error_response(f"获取AI设置失败: {str(e)}", 500)

# 项目管理API
@api_bp.route('/projects', methods=['POST'])
def create_project():
    """创建写作项目"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        if not data:
            return error_response("请求数据不能为空", 400)
        
        # 调试日志
        print(f"创建项目请求数据: {data}")
        
        title = data.get('title')
        article_type = data.get('article_type')
        subject = data.get('subject')
        topic_mode = data.get('topic_mode', 'custom')
        custom_topic = data.get('custom_topic', '')
        
        # 验证必填字段
        if not title or not title.strip():
            return error_response("项目标题不能为空")
        
        if not article_type or not article_type.strip():
            return error_response("文章类型不能为空")
        
        if not subject or not subject.strip():
            return error_response("学科不能为空")
        
        # 获取用户信息
        @with_user_dao
        def _get_user(dao):
            return dao.get_user_by_id(user_id)
        
        user = _get_user()
        if not user:
            return error_response("用户不存在", 404)
        
        # 生成或使用自定义题目
        if topic_mode == 'ai_generated':
            # 如果前端已经生成了题目并通过custom_topic传递，直接使用
            if custom_topic and custom_topic.strip():
                topic = custom_topic
                print(f"使用前端已生成的AI题目: {topic}")
            else:
                # 前端没有生成题目，后端生成
                try:
                    # 获取用户AI设置
                    user_ai_settings = get_user_ai_settings(user_id)
                    print(f"AI设置: {user_ai_settings}")
                    
                    # 检查AI设置是否完整
                    if not user_ai_settings.get('provider') or not user_ai_settings.get('model'):
                        return error_response("AI生成题目需要先配置AI设置（供应商和模型）。请在首页配置AI设置后再试，或选择自定义题目模式。")
                    
                    topic = sync_generate_topic(
                        grade=user.get('grade'),
                        subject=subject,
                        article_type=article_type,
                        user_settings=user_ai_settings
                    )
                    print(f"后端生成的题目: {topic}")
                except Exception as e:
                    print(f"AI生成题目失败: {str(e)}")
                    return error_response(f"AI生成题目失败: {str(e)}")
        else:
            topic = custom_topic
            if not topic or not topic.strip():
                return error_response("自定义题目不能为空")
        
        # 验证题目
        if not topic or not topic.strip():
            return error_response("题目不能为空")
        
        print(f"创建项目参数: user_id={user_id}, title={title}, topic={topic}, article_type={article_type}, subject={subject}, grade={user.get('grade')}")
        
        # 创建项目
        @with_project_dao
        def _create_project(dao):
            project = dao.create_project(user_id, title, topic, article_type, subject, user.get('grade', '初中'))
            return project  # JSON DAO直接返回字典
        
        project_data = _create_project()
        print(f"创建的项目: {project_data}")
        
        return success_response(project_data, "项目创建成功")
        
    except Exception as e:
        print(f"创建项目异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f"创建项目失败: {str(e)}", 500)

@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """获取项目列表"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        status = request.args.get('status')
        
        @with_project_dao
        def _get_projects(dao):
            projects = dao.get_projects_by_user(user_id, status)
            return projects  # JSON DAO直接返回字典列表
        
        projects_data = _get_projects()
        
        return success_response(projects_data)
        
    except Exception as e:
        return error_response(f"获取项目列表失败: {str(e)}", 500)

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        @with_project_dao
        def _get_project(dao):
            project = dao.get_project_by_id(project_id)
            if project and project.get('user_id') == user_id:
                return project  # JSON DAO直接返回字典
            return None
        
        project_data = _get_project()
        
        if not project_data:
            return error_response("项目不存在", 404)
        
        return success_response(project_data)
        
    except Exception as e:
        return error_response(f"获取项目详情失败: {str(e)}", 500)

@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        
        @with_project_dao
        def _update_project(dao):
            # 验证项目所有权
            project = dao.get_project_by_id(project_id)
            if not project or project.get('user_id') != user_id:
                return None
            
            # 更新内容
            for field in ['brainstorm_content', 'outline_content', 'writing_content']:
                if field in data:
                    dao.update_project_content(project_id, field, data[field])
            
            # 更新状态
            if 'status' in data:
                dao.update_project_status(project_id, data['status'])
            
            # 更新评分
            if 'stage_ratings' in data:
                stage_ratings = data['stage_ratings']
                # 计算总分：将星级评分(1-5)转换为百分制(20-100)
                valid_ratings = [rating for rating in stage_ratings.values() if rating > 0]
                if valid_ratings:
                    avg_star_rating = sum(valid_ratings) / len(valid_ratings)
                    overall_score = int(avg_star_rating * 20)  # 1星=20分, 5星=100分
                else:
                    overall_score = 0
                dao.save_scores(project_id, overall_score, stage_ratings)
            
            # 返回更新后的项目
            updated_project = dao.get_project_by_id(project_id)
            return updated_project  # JSON DAO直接返回字典
        
        project_data = _update_project()
        
        if not project_data:
            return error_response("项目不存在", 404)
        
        return success_response(project_data, "项目更新成功")
        
    except Exception as e:
        return error_response(f"更新项目失败: {str(e)}", 500)

@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        @with_project_dao
        def _delete_project(dao):
            # 验证项目所有权
            project = dao.get_project_by_id(project_id)
            if not project or project.get('user_id') != user_id:
                return False
            
            return dao.delete_project(project_id)
        
        success = _delete_project()
        
        if not success:
            return error_response("项目不存在", 404)
        
        return success_response(message="项目删除成功")
        
    except Exception as e:
        return error_response(f"删除项目失败: {str(e)}", 500)

# AI功能API
@api_bp.route('/ai/generate-topic', methods=['POST'])
def generate_topic():
    """生成写作题目"""
    try:
        # 检查用户登录状态
        user_id = session.get('user_id')
        if not user_id:
            return error_response("请先登录", 401)
        
        data = request.get_json()
        grade = data.get('grade')
        subject = data.get('subject')
        article_type = data.get('article_type')
        requirement = data.get('requirement', '')
        
        if not grade or not subject or not article_type:
            return error_response("年级、学科和文章类型不能为空")
        
        # 获取用户AI设置
        user_ai_settings = get_user_ai_settings(user_id)
        
        # 生成题目
        topic = sync_generate_topic(
            grade=grade,
            subject=subject,
            article_type=article_type,
            user_settings=user_ai_settings,
            requirement=requirement
        )
        
        return success_response({'topic': topic})
        
    except Exception as e:
        return error_response(f"生成题目失败: {str(e)}", 500)

@api_bp.route('/ai/analyze', methods=['POST'])
def analyze_content():
    """分析写作内容"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        content = data.get('content')
        stage = data.get('stage', 'writing')
        project_id = data.get('project_id')
        
        # 允许空内容，给出最低评分
        if not content:
            content = ""  # 空内容处理
        
        # 获取用户信息
        @with_user_dao
        def _get_user_data(dao):
            user = dao.get_user_by_id(user_id)
            return user  # JSON DAO直接返回字典
        
        user_data = _get_user_data()
        if not user_data:
            return error_response("用户不存在", 404)
        
        # 获取项目信息
        project_data = None
        if project_id:
            @with_project_dao
            def _get_project_data(dao):
                proj = dao.get_project_by_id(project_id)
                return proj if proj and proj.get('user_id') == user_id else None
            
            project_data = _get_project_data()
        
        # 构建AI上下文 - 优先使用项目的年级和学科信息
        if project_data:
            # 使用项目的年级和学科信息
            context = {
                'grade': project_data.get('grade', user_data['grade']),
                'subject': project_data.get('subject', user_data['subject']),
                'content': content,
                'stage': stage,
                'topic': project_data['topic'],
                'article_type': project_data['article_type'],
                'title': project_data['title']
            }
        else:
            # 没有项目信息时使用用户设置
            context = {
                'grade': user_data['grade'],
                'subject': user_data['subject'],
                'content': content,
                'stage': stage
            }
        
        # 获取用户AI设置
        user_ai_settings = get_user_ai_settings(user_id)
        
        # 分析内容
        analysis = sync_analyze_content(
            content=content,
            stage=stage,
            context=context,
            user_settings=user_ai_settings
        )
        
        # 保存反馈到项目
        if project_id:
            @with_project_dao
            def _save_feedback(dao):
                project = dao.get_project_by_id(project_id)
                if project and project.get('user_id') == user_id:
                    # 更新项目的反馈信息
                    feedback_data = json.loads(project.get('ai_feedback', '{}') or '{}')
                    feedback_data[f'{stage}_analysis'] = analysis
                    # 使用DAO更新项目
                    dao.save_ai_feedback(project_id, feedback_data)
                    return True
                return False
            
            _save_feedback()
        
        return success_response(analysis)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f"分析内容失败: {str(e)}", 500)

@api_bp.route('/ai/evaluate', methods=['POST'])
def evaluate_article():
    """评估文章质量"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        content = data.get('content')
        project_id = data.get('project_id')
        
        if not content:
            return error_response("内容不能为空")
        
        # 获取用户信息
        @with_user_dao
        def _get_user_data(dao):
            user = dao.get_user_by_id(user_id)
            return user  # JSON DAO直接返回字典
        
        user_data = _get_user_data()
        if not user_data:
            return error_response("用户不存在", 404)
        
        # 获取项目信息
        project_data = None
        if project_id:
            @with_project_dao
            def _get_project_data(dao):
                proj = dao.get_project_by_id(project_id)
                return proj if proj and proj.get('user_id') == user_id else None
            
            project_data = _get_project_data()
        
        # 构建AI上下文 - 优先使用项目的年级和学科信息
        if project_data:
            # 使用项目的年级和学科信息
            context = {
                'grade': project_data.get('grade', user_data.get('grade', '')),
                'subject': project_data.get('subject', user_data.get('subject', '')),
                'content': content,
                'evaluation_type': 'comprehensive',
                'topic': project_data.get('topic', ''),
                'article_type': project_data.get('article_type', ''),
                'title': project_data.get('title', '')
            }
        else:
            # 没有项目信息时使用用户设置
            context = {
                'grade': user_data.get('grade', ''),
                'subject': user_data.get('subject', ''),
                'content': content,
                'evaluation_type': 'comprehensive'
            }
        
        # 获取用户AI设置
        user_ai_settings = get_user_ai_settings(user_id)
        
        # 评估文章
        evaluation = sync_evaluate_article(
            content=content,
            context=context,
            user_settings=user_ai_settings
        )
        
        # 保存评估结果到项目
        if project_id:
            @with_project_dao
            def _save_scores(dao):
                project = dao.get_project_by_id(project_id)
                if project and project.get('user_id') == user_id:
                    # 更新项目的评估信息
                    scores_str = project.get('scores', '{}')
                    if not scores_str or scores_str.strip() == '':
                        scores_str = '{}'
                    scores_data = json.loads(scores_str)
                    scores_data['ai_evaluation'] = evaluation
                    # 使用DAO更新项目
                    dao.save_scores(project_id, 0, scores_data)
                    return True
                return False
            
            _save_scores()
        
        return success_response(evaluation)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f"评估文章失败: {str(e)}", 500)

@api_bp.route('/ai/suggestions', methods=['POST'])
def generate_suggestions():
    """生成写作建议"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        content = data.get('content', '')
        stage = data.get('stage', 'writing')
        topic = data.get('topic', '')
        grade = data.get('grade', '初中')
        subject = data.get('subject', '语文')
        project_id = data.get('project_id')
        
        # 获取用户信息
        @with_user_dao
        def _get_user_data(dao):
            user = dao.get_user_by_id(user_id)
            return user  # JSON DAO直接返回字典
        
        user_data = _get_user_data()
        if not user_data:
            return error_response("用户不存在", 404)
        
        # 获取项目信息
        project_data = None
        if project_id:
            @with_project_dao
            def _get_project_data(dao):
                proj = dao.get_project_by_id(project_id)
                return proj if proj and proj.get('user_id') == user_id else None
            
            project_data = _get_project_data()
        
        # 获取完整内容和当前阶段文本
        full_content = data.get('full_content', {})
        current_stage_text = data.get('current_stage_text', stage)
        
        # 构建AI上下文 - 优先使用项目的年级和学科信息
        if project_data:
            # 使用项目的年级和学科信息
            context = {
                'grade': project_data.get('grade', user_data['grade']),
                'subject': project_data.get('subject', user_data['subject']),
                'content': content,
                'stage': stage,
                'topic': project_data['topic'],
                'article_type': project_data['article_type'],
                'title': project_data['title'],
                'full_content': full_content,
                'current_stage_text': current_stage_text
            }
        else:
            # 没有项目信息时使用传入参数或用户设置
            context = {
                'grade': grade or user_data['grade'],
                'subject': subject or user_data['subject'],
                'content': content,
                'stage': stage,
                'topic': topic,
                'full_content': full_content,
                'current_stage_text': current_stage_text
            }
        
        # 获取用户AI设置
        user_ai_settings = get_user_ai_settings(user_id)
        
        # 生成阶段特定的建议
        suggestions = sync_generate_stage_suggestions(
            content=content,
            stage=stage,
            context=context,
            user_settings=user_ai_settings
        )
        
        return success_response(suggestions)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f"生成建议失败: {str(e)}", 500)

# AI配置相关API
@api_bp.route('/ai/models/ollama', methods=['GET'])
def get_ollama_models():
    """获取Ollama模型列表"""
    try:
        # 导入Ollama工具
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'llm-api'))
        
        from ollama_utils import OllamaManager
        
        # 获取自定义base_url
        custom_base_url = request.args.get('base_url')
        
        if custom_base_url:
            ollama_manager = OllamaManager(base_url=custom_base_url)
        else:
            ollama_manager = OllamaManager()
            
        if not ollama_manager.is_server_running():
            return error_response("Ollama服务器未运行")
        
        models = ollama_manager.get_locally_available_models()
        return success_response(models)
        
    except ImportError:
        return error_response("Ollama工具未安装")
    except Exception as e:
        return error_response(f"获取Ollama模型失败: {str(e)}")

@api_bp.route('/ai/models/lmstudio', methods=['GET'])
def get_lmstudio_models():
    """获取LM Studio模型列表"""
    try:
        # 导入LM Studio工具
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'llm-api'))
        
        from lmstudio_utils import LMStudioManager
        
        # 获取自定义base_url
        custom_base_url = request.args.get('base_url')
        
        if custom_base_url:
            lmstudio_manager = LMStudioManager(base_url=custom_base_url)
        else:
            lmstudio_manager = LMStudioManager()
            
        if not lmstudio_manager.is_server_running():
            return error_response("LM Studio服务器未运行")
        
        models = lmstudio_manager.get_model_names()
        return success_response(models)
        
    except ImportError:
        return error_response("LM Studio工具未安装")
    except Exception as e:
        return error_response(f"获取LM Studio模型失败: {str(e)}")

@api_bp.route('/ai/test', methods=['POST'])
def test_ai_connection():
    """测试AI连接"""
    try:
        data = request.get_json()
        user_settings = {
            'provider': data.get('provider'),
            'model': data.get('model'),
            'api_key': data.get('api_key'),
            'base_url': data.get('base_url')
        }
        
        if not user_settings['provider'] or not user_settings['model']:
            return error_response("供应商和模型不能为空")
        
        # 测试连接
        success = sync_test_connection(user_settings)
        
        if success:
            return success_response({
                'model_info': {
                    'provider': user_settings['provider'],
                    'model': user_settings['model'],
                    'base_url': user_settings['base_url']
                }
            }, "AI连接测试成功")
        else:
            return error_response("AI连接测试失败")
        
    except Exception as e:
        return error_response(f"AI连接测试失败: {str(e)}")

@api_bp.route('/ai/score_article', methods=['POST'])
def score_article():
    """使用新的评分标准对文章进行评分"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        article_data = data.get('article_data', {})
        project_id = data.get('project_id')
        
        if not article_data:
            return error_response("文章数据不能为空")
        
        # 获取用户信息
        @with_user_dao
        def _get_user_data(dao):
            user = dao.get_user_by_id(user_id)
            return user
        
        user_data = _get_user_data()
        if not user_data:
            return error_response("用户不存在", 404)
        
        # 获取项目信息
        project_data = None
        if project_id:
            @with_project_dao
            def _get_project_data(dao):
                proj = dao.get_project_by_id(project_id)
                return proj if proj and proj.get('user_id') == user_id else None
            
            project_data = _get_project_data()
        
        # 获取用户AI设置
        user_ai_settings = get_user_ai_settings(user_id)
        
        # 创建AI服务实例
        ai_service = AIService()
        
        # 创建评分服务实例
        scoring_service = ScoringService(ai_service)
        
        # 使用异步评分（在同步上下文中调用）
        import asyncio
        
        async def _score_article():
            return await scoring_service.score_article(article_data, user_ai_settings)
        
        # 在新的事件循环中运行异步函数
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果事件循环正在运行，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _score_article())
                result = future.result()
        else:
            result = loop.run_until_complete(_score_article())
        
        if result and 'scores' in result:
            return success_response({
                'scores': result['scores'],
                'stage_reasons': result.get('stage_reasons', {}),
                'summary': result.get('summary', {}),
                'timestamp': result.get('timestamp')
            }, "文章评分完成")
        else:
            return error_response("评分失败，请检查内容或AI设置")
            
    except Exception as e:
        print(f"评分错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(f"评分失败: {str(e)}", 500)