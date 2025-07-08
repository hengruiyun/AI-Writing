"""
文章评分服务
Article Scoring Service

集成LLM评分功能，实现新的文章打分标准
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Tuple, List
from article_scoring_standards import ArticleScoringStandards
from ai_service import AIService

class ScoringService:
    """文章评分服务类"""
    
    def __init__(self, ai_service: AIService = None):
        """
        初始化评分服务
        
        Args:
            ai_service: AI服务实例
        """
        self.ai_service = ai_service or AIService()
        self.standards = ArticleScoringStandards()
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载评分配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'scoring_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"评分配置文件不存在: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"评分配置文件格式错误: {e}")
            return {}
    
    async def score_content(self, stage: str, content: str, user_settings: Optional[Dict] = None) -> Tuple[int, str]:
        """
        对内容进行评分
        
        Args:
            stage: 评分阶段 ('brainstorm', 'outline', 'writing', 'highlight')
            content: 待评分内容
            user_settings: 用户AI设置
        
        Returns:
            tuple: (评分(0-100), 评分理由)
        """
        if not content or not content.strip():
            return 0, "内容为空，无法评分"
        
        try:
            # 获取评分标准
            if stage not in self.standards.SCORING_CRITERIA:
                return 0, f"未知的评分阶段: {stage}"
            
            criteria = self.standards.SCORING_CRITERIA[stage]
            
            # 构建评分提示词
            prompt_parts = [f"请根据以下标准对内容进行评分（0-100分）："]
            prompt_parts.append(f"\n评分标准：\n{criteria['description']}")
            prompt_parts.append(f"\n评分要点：\n{chr(10).join([f'- {point}' for point in criteria['criteria']])}")
            
            # 添加详细要求（如果存在）
            if 'detailed_requirements' in criteria:
                prompt_parts.append("\n详细评分要求：")
                for category, requirements in criteria['detailed_requirements'].items():
                    prompt_parts.append(f"\n{category}：")
                    for item, desc in requirements.items():
                        prompt_parts.append(f"  - {item}：{desc}")
            
            # 添加相似度评分规则（构思评分专用）
            if 'similarity_scoring' in criteria:
                prompt_parts.append("\n相似度评分规则：")
                for key, value in criteria['similarity_scoring'].items():
                    if isinstance(value, dict):
                        prompt_parts.append(f"\n{key}：")
                        for sub_key, sub_value in value.items():
                            prompt_parts.append(f"  - {sub_key}：{sub_value}")
                    else:
                        prompt_parts.append(f"- {key}：{value}")
            
            # 添加评估流程（构思评分专用）
            if 'evaluation_process' in criteria:
                prompt_parts.append("\n评估流程：")
                for step, desc in criteria['evaluation_process'].items():
                    prompt_parts.append(f"- {step}：{desc}")
            
            # 添加创新指数（爆点评分专用）
            if 'innovation_index' in criteria:
                prompt_parts.append("\n创新指数评级：")
                for level, desc in criteria['innovation_index'].items():
                    prompt_parts.append(f"- {level}：{desc}")
            
            # 添加常见写法扣分规则（爆点评分专用）
            if 'common_patterns_penalty' in criteria:
                prompt_parts.append("\n常见写法扣分规则：")
                for pattern, penalty in criteria['common_patterns_penalty'].items():
                    prompt_parts.append(f"- {pattern}：{penalty}")
            
            # 添加创新加分规则（爆点评分专用）
            if 'innovation_bonus' in criteria:
                prompt_parts.append("\n创新表现加分规则：")
                for bonus_type, bonus_desc in criteria['innovation_bonus'].items():
                    prompt_parts.append(f"- {bonus_type}：{bonus_desc}")
            
            # 添加扣分规则（正文评分专用）
            if 'deduction_rules' in criteria:
                prompt_parts.append("\n扣分规则：")
                for rule, desc in criteria['deduction_rules'].items():
                    prompt_parts.append(f"- {rule}：{desc}")
            
            prompt_parts.append(f"\n待评分内容：\n{content}")
            
            # 构思评分需要特殊说明
            if stage == 'brainstorm':
                prompt_parts.append("\n特别说明：")
                prompt_parts.append("- 如果同时提供了正文内容，请先将正文总结为一段话")
                prompt_parts.append("- 然后计算正文摘要与构思内容的相似度百分比")
                prompt_parts.append("- 相似度百分比直接作为构思得分（如相似度50%得50分）")
                prompt_parts.append("- 在理由中详细说明相似度分析过程")
            
            prompt_parts.append("\n请按以下格式回复：\n评分：[0-100的数字]\n理由：[详细的评分理由，说明各项要求的达成情况]")
            
            prompt = "".join(prompt_parts)
            
            # 使用quick_generate进行评分
            from fast_client import quick_generate
            from models import ModelProvider, LLMModel
            
            # 创建模型配置
            settings = user_settings or {}
            try:
                provider = ModelProvider(settings.get('provider', 'ollama'))
            except ValueError:
                provider = ModelProvider.OLLAMA
            
            model = LLMModel(
                display_name=settings.get('model', 'llama3.2'),
                model_name=settings.get('model', 'llama3.2'),
                provider=provider
            )
            
            # 添加API配置
            if hasattr(model, 'api_key'):
                model.api_key = settings.get('api_key', '')
            if hasattr(model, 'base_url'):
                model.base_url = settings.get('base_url', '')
            else:
                # 如果模型没有base_url属性，动态添加
                setattr(model, 'api_key', settings.get('api_key', ''))
                setattr(model, 'base_url', settings.get('base_url', ''))
            
            # 调用AI进行评分
            response = quick_generate(
                prompt=prompt,
                model=model,
                max_tokens=500,
                temperature=0.3
            )
            
            # 记录AI返回的原始内容
            self.logger.info(f"阶段 {stage} AI返回内容: {response}")
            
            # 解析评分结果
            score, reason = self._parse_scoring_response(response)
            
            self.logger.info(f"阶段 {stage} 评分完成: {score}分")
            return score, reason
            
        except Exception as e:
            self.logger.error(f"评分过程中发生错误: {e}")
            return 0, f"评分失败: {str(e)}"
    
    async def score_content_with_context(self, stage: str, content: str, article_data: Dict[str, str], user_settings: Optional[Dict] = None) -> Tuple[int, str]:
        """
        对内容进行评分（带上下文，主要用于构思评分）
        
        Args:
            stage: 评分阶段
            content: 待评分内容（构思内容）
            article_data: 完整文章数据，包含正文内容
            user_settings: 用户AI设置
        
        Returns:
            tuple: (评分(0-100), 评分理由)
        """
        if not content or not content.strip():
            return 0, "内容为空，无法评分"
        
        try:
            # 获取评分标准
            if stage not in self.standards.SCORING_CRITERIA:
                return 0, f"未知的评分阶段: {stage}"
            
            criteria = self.standards.SCORING_CRITERIA[stage]
            
            # 构建评分提示词
            prompt_parts = [f"请根据以下标准对内容进行评分（0-100分）："]
            prompt_parts.append(f"\n评分标准：\n{criteria['description']}")
            prompt_parts.append(f"\n评分要点：\n{chr(10).join([f'- {point}' for point in criteria['criteria']])}")
            
            # 添加详细要求（如果存在）
            if 'detailed_requirements' in criteria:
                prompt_parts.append("\n详细评分要求：")
                for category, requirements in criteria['detailed_requirements'].items():
                    prompt_parts.append(f"\n{category}：")
                    for item, desc in requirements.items():
                        prompt_parts.append(f"  - {item}：{desc}")
            
            # 添加相似度评分规则（构思评分专用）
            if 'similarity_scoring' in criteria:
                prompt_parts.append("\n相似度评分规则：")
                for key, value in criteria['similarity_scoring'].items():
                    if isinstance(value, dict):
                        prompt_parts.append(f"\n{key}：")
                        for sub_key, sub_value in value.items():
                            prompt_parts.append(f"  - {sub_key}：{sub_value}")
                    else:
                        prompt_parts.append(f"- {key}：{value}")
            
            # 添加评估流程（构思评分专用）
            if 'evaluation_process' in criteria:
                prompt_parts.append("\n评估流程：")
                for step, desc in criteria['evaluation_process'].items():
                    prompt_parts.append(f"- {step}：{desc}")
            
            prompt_parts.append(f"\n构思内容：\n{content}")
            
            # 如果有正文内容，添加到提示词中
            writing_content = article_data.get('writing', '')
            if writing_content and writing_content.strip():
                prompt_parts.append(f"\n正文内容：\n{writing_content}")
                prompt_parts.append("\n请按照评估流程：")
                prompt_parts.append("1. 先将正文内容总结为一段话")
                prompt_parts.append("2. 计算正文摘要与构思内容的相似度百分比")
                prompt_parts.append("3. 相似度百分比直接作为构思得分")
                prompt_parts.append("4. 在理由中详细说明相似度分析过程")
            else:
                prompt_parts.append("\n注意：未提供正文内容，无法进行相似度比较，请提供构思内容以便评分。")
            
            prompt_parts.append("\n请按以下格式回复：\n评分：[0-100的数字]\n理由：[详细的评分理由，说明各项要求的达成情况]")
            
            prompt = "".join(prompt_parts)
            
            # 使用quick_generate进行评分
            from fast_client import quick_generate
            from models import ModelProvider, LLMModel
            
            # 创建模型配置
            settings = user_settings or {}
            try:
                provider = ModelProvider(settings.get('provider', 'ollama'))
            except ValueError:
                provider = ModelProvider.OLLAMA
            
            model = LLMModel(
                display_name=settings.get('model', 'llama3.2'),
                model_name=settings.get('model', 'llama3.2'),
                provider=provider
            )
            
            # 添加API配置
            if hasattr(model, 'api_key'):
                model.api_key = settings.get('api_key', '')
            if hasattr(model, 'base_url'):
                model.base_url = settings.get('base_url', '')
            else:
                # 如果模型没有base_url属性，动态添加
                setattr(model, 'api_key', settings.get('api_key', ''))
                setattr(model, 'base_url', settings.get('base_url', ''))
            
            # 调用AI进行评分
            response = quick_generate(
                prompt=prompt,
                model=model,
                max_tokens=500,
                temperature=0.3
            )
            
            # 记录AI返回的原始内容
            self.logger.info(f"阶段 {stage} (带上下文) AI返回内容: {response}")
            
            # 解析评分结果
            score, reason = self._parse_scoring_response(response)
            
            self.logger.info(f"阶段 {stage} (带上下文) 评分完成: {score}分")
            return score, reason
            
        except Exception as e:
            self.logger.error(f"评分过程中发生错误: {e}")
            return 0, f"评分失败: {str(e)}"
    
    def _parse_scoring_response(self, response: str) -> Tuple[int, str]:
        """
        解析AI评分响应
        
        Args:
            response: AI响应文本
        
        Returns:
            tuple: (评分, 理由)
        """
        try:
            lines = response.strip().split('\n')
            score = 0
            reason = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('评分：') or line.startswith('评分:'):
                    # 提取评分数字
                    score_text = line.split('：')[-1].split(':')[-1].strip()
                    score_text = score_text.replace('分', '').strip()
                    try:
                        score = int(float(score_text))
                        score = max(0, min(100, score))  # 限制在0-100范围内
                    except ValueError:
                        score = 0
                elif line.startswith('理由：') or line.startswith('理由:'):
                    reason = line.split('：')[-1].split(':')[-1].strip()
                elif reason and line:
                    reason += '\n' + line
            
            if not reason:
                reason = response.strip()
            
            return score, reason
            
        except Exception as e:
            self.logger.error(f"解析评分响应失败: {e}")
            return 0, f"解析失败: {str(e)}"
    
    async def score_article(self, article_data: Dict[str, str], user_settings: Optional[Dict] = None) -> Dict[str, Any]:
        """
        对整篇文章进行评分
        
        Args:
            article_data: 文章数据 {'brainstorm': '', 'outline': '', 'writing': '', 'highlight': ''}
            user_settings: 用户AI设置
        
        Returns:
            dict: 评分结果
        """
        results = {
            'scores': {},
            'stage_reasons': {},
            'total_score': 0,
            'breakdown': {},
            'timestamp': self._get_timestamp()
        }
        
        # 逐阶段评分
        for stage, content in article_data.items():
            if stage in self.standards.STAGE_WEIGHTS:
                # 构思评分需要特殊处理，传递正文内容用于相似度比较
                if stage == 'brainstorm':
                    score, reason = await self.score_content_with_context(stage, content, article_data, user_settings)
                else:
                    score, reason = await self.score_content(stage, content, user_settings)
                results['scores'][stage] = score
                results['stage_reasons'][stage] = reason
        
        # 计算总分
        if results['scores']:
            results['total_score'] = self.standards.calculate_total_score(results['scores'])
            results['breakdown'] = self.standards.get_score_breakdown(results['scores'])
        
        return results
    
    def get_scoring_summary(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """
        获取评分摘要
        
        Args:
            scores: 各阶段评分
        
        Returns:
            dict: 评分摘要
        """
        total_score = self.standards.calculate_total_score(scores)
        breakdown = self.standards.get_score_breakdown(scores)
        
        # 确定总体评级
        score_level = self._get_score_level(total_score)
        
        return {
            'total_score': total_score,
            'score_level': score_level,
            'breakdown': breakdown,
            'weights': self.standards.get_all_weights(),
            'recommendations': self._get_recommendations(scores)
        }
    
    def _get_score_level(self, score: float) -> Dict[str, str]:
        """获取评分等级"""
        scoring_levels = self.config.get('scoring_levels', {})
        
        for level, config in scoring_levels.items():
            score_range = config.get('range', [0, 0])
            if score_range[0] <= score <= score_range[1]:
                return {
                    'level': level,
                    'label': config.get('label', ''),
                    'description': config.get('description', '')
                }
        
        return {
            'level': 'unknown',
            'label': '未知',
            'description': '无法确定评分等级'
        }
    
    def _get_recommendations(self, scores: Dict[str, int]) -> List[str]:
        """获取改进建议"""
        recommendations = []
        
        # 根据各阶段评分给出建议
        for stage, score in scores.items():
            if score < 60:
                stage_name = self.config.get('stage_weights', {}).get(stage, {}).get('name', stage)
                recommendations.append(f"{stage_name}部分需要重点改进（当前{score}分）")
            elif score < 80:
                stage_name = self.config.get('stage_weights', {}).get(stage, {}).get('name', stage)
                recommendations.append(f"{stage_name}部分有提升空间（当前{score}分）")
        
        # 根据权重给出重点关注建议
        weighted_scores = {}
        for stage, score in scores.items():
            if stage in self.standards.STAGE_WEIGHTS:
                weighted_scores[stage] = score * self.standards.STAGE_WEIGHTS[stage]
        
        if weighted_scores:
            lowest_weighted = min(weighted_scores, key=weighted_scores.get)
            if weighted_scores[lowest_weighted] < 30:  # 加权分数低于30
                stage_name = self.config.get('stage_weights', {}).get(lowest_weighted, {}).get('name', lowest_weighted)
                recommendations.append(f"建议重点关注{stage_name}部分，其权重较高且得分较低")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_scoring_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证评分数据
        
        Args:
            data: 评分数据
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        required_fields = ['stage_scores', 'total_score']
        
        for field in required_fields:
            if field not in data:
                return False, f"缺少必需字段: {field}"
        
        # 验证阶段评分
        stage_scores = data.get('stage_scores', {})
        is_valid, error_msg = self.standards.validate_scores(stage_scores)
        if not is_valid:
            return False, error_msg
        
        # 验证总分
        total_score = data.get('total_score', 0)
        if not isinstance(total_score, (int, float)) or not 0 <= total_score <= 100:
            return False, "总分必须是0-100之间的数字"
        
        return True, ""
    
    def export_scoring_report(self, article_id: str, scoring_data: Dict[str, Any]) -> str:
        """
        导出评分报告
        
        Args:
            article_id: 文章ID
            scoring_data: 评分数据
        
        Returns:
            str: 报告内容
        """
        report = f"""
文章评分报告
============

文章ID: {article_id}
评分时间: {scoring_data.get('timestamp', 'N/A')}
总分: {scoring_data.get('total_score', 0):.1f}分

详细评分:
"""
        
        breakdown = scoring_data.get('breakdown', {})
        if 'stages' in breakdown:
            for stage, info in breakdown['stages'].items():
                report += f"- {info['name']}: {info['raw_score']}分 (权重{info['percentage']}) = {info['weighted_score']:.1f}分\n"
        
        # 添加评分理由
        stage_reasons = scoring_data.get('stage_reasons', {})
        if stage_reasons:
            report += "\n评分理由:\n"
            for stage, reason in stage_reasons.items():
                stage_name = self.config.get('stage_weights', {}).get(stage, {}).get('name', stage)
                report += f"\n{stage_name}:\n{reason}\n"
        
        return report


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_scoring():
        """测试评分功能"""
        scoring_service = ScoringService()
        
        # 测试文章数据
        article_data = {
            'brainstorm': '这是一个关于人工智能发展的文章构思，主要探讨AI在教育领域的应用前景...',
            'outline': '一、引言\n二、AI在教育中的现状\n三、未来发展趋势\n四、挑战与机遇\n五、结论',
            'writing': '人工智能技术正在深刻改变着教育行业的面貌。从个性化学习到智能辅导，AI技术为教育带来了前所未有的机遇...',
            'highlight': '本文的创新点在于提出了"AI+教育"的三层架构模型，为教育行业的数字化转型提供了新的思路。'
        }
        
        # 执行评分
        results = await scoring_service.score_article(article_data)
        
        print("评分结果:")
        print(f"总分: {results['total_score']}")
        print("\n各阶段评分:")
        for stage, score in results['stage_scores'].items():
            print(f"{stage}: {score}分")
        
        # 获取评分摘要
        summary = scoring_service.get_scoring_summary(results['stage_scores'])
        print(f"\n评分等级: {summary['score_level']['label']}")
        print(f"等级描述: {summary['score_level']['description']}")
        
        if summary['recommendations']:
            print("\n改进建议:")
            for rec in summary['recommendations']:
                print(f"- {rec}")
    
    # 运行测试
    asyncio.run(test_scoring())