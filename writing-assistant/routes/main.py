"""
主页面路由模块
处理页面渲染
"""
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from json_dao import ProjectDAO, UserDAO, with_project_dao, with_user_dao, dicts_to_projects
from article_scoring_standards import ArticleScoringStandards
import json

# 创建主页面蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页 - 重定向到项目页面"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    return redirect(url_for('main.projects'))

@main_bp.route('/login')
def login():
    """登录页面 - 直接重定向到项目页面"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    return redirect(url_for('main.projects'))

@main_bp.route('/setup')
def setup():
    """项目设置页面"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    return render_template('setup.html')

# 登录页面已删除

@main_bp.route('/projects')
def projects():
    """项目列表页面"""
    # 自动设置为已登录状态
    if 'user_id' not in session:
        session['user_id'] = 1
        session['username'] = '267278466@qq.com'
    
    user_id = session.get('user_id')
    
    try:
        @with_project_dao
        def _get_projects(dao):
            projects = dao.get_projects_by_user(user_id)
            # 重新计算每个项目的总分
            for project in projects:
                if project.get('scores'):
                    try:
                        scores_dict = json.loads(project['scores'])
                        # 将星级评分转换为百分制评分
                        percentage_scores = {}
                        for stage, star_rating in scores_dict.items():
                            percentage_scores[stage] = star_rating * 20  # 5星制转100分制
                        
                        # 重新计算总分
                        new_total_score = ArticleScoringStandards.calculate_total_score(percentage_scores)
                        project['final_score'] = new_total_score
                    except (json.JSONDecodeError, ValueError):
                        pass  # 保持原有分数
            return projects  # JSON DAO直接返回字典列表
        
        projects_data = _get_projects()
        
        return render_template('projects.html', projects=projects_data)
        
    except Exception as e:
        flash(f'获取项目列表失败: {str(e)}', 'error')
        return render_template('projects.html', projects=[])

@main_bp.route('/writing/<int:project_id>')
def writing(project_id):
    """写作页面"""
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
                # 重新计算总分
                if project.get('scores'):
                    try:
                        scores_dict = json.loads(project['scores'])
                        # 将星级评分转换为百分制评分
                        percentage_scores = {}
                        for stage, star_rating in scores_dict.items():
                            percentage_scores[stage] = star_rating * 20  # 5星制转100分制
                        
                        # 重新计算总分
                        new_total_score = ArticleScoringStandards.calculate_total_score(percentage_scores)
                        project['final_score'] = new_total_score
                    except (json.JSONDecodeError, ValueError):
                        pass  # 保持原有分数
                return project  # JSON DAO直接返回字典
            return None
        
        project_data = _get_project()
        
        if not project_data:
            flash('项目不存在', 'error')
            return redirect(url_for('main.projects'))
        
        return render_template('writing.html', project=project_data)
        
    except Exception as e:
        flash(f'获取项目信息失败: {str(e)}', 'error')
        return redirect(url_for('main.projects'))

@main_bp.route('/review/<int:project_id>')
def review(project_id):
    """评阅页面"""
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
            flash('项目不存在', 'error')
            return redirect(url_for('main.projects'))
        
        return render_template('review.html', project=project_data)
        
    except Exception as e:
        flash(f'获取项目信息失败: {str(e)}', 'error')
        return redirect(url_for('main.projects'))

# 登出功能已删除