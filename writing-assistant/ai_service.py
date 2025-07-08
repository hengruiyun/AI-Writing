"""
AI服务模块
使用快速客户端统一调用AI API，支持完整上下文传递
"""
import sys
import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from config import get_config

# 配置调试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 添加llm-api到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'llm-api'))

from fast_client import quick_generate, quick_test
from models import ModelProvider, LLMModel

config = get_config()

class AIService:
    """AI服务类 - 统一上下文处理"""
    
    def __init__(self):
        self.timeout = config.LLM_TIMEOUT
        # 默认AI设置
        self.default_settings = {
            'provider': '',
            'model': '',
            'api_key': '',
            'base_url': ''
        }
        
    
    def _get_ai_settings(self, user_settings: Optional[Dict] = None) -> Dict[str, Any]:
        """获取AI设置"""
        if user_settings:
            return user_settings
        return self.default_settings
    
    def _create_llm_model(self, settings: Dict) -> LLMModel:
        """创建LLM模型对象"""
        try:
            provider = ModelProvider(settings['provider'])
        except ValueError:
            provider = ModelProvider.OLLAMA
        
        model = LLMModel(
            display_name=settings['model'],
            model_name=settings['model'],
            provider=provider
        )
        
        # 处理base_url格式化
        base_url = settings.get('base_url', '')
        if base_url and not base_url.startswith(('http://', 'https://')):
            # 自动添加http://协议前缀
            base_url = f'http://{base_url}'
            logger.debug(f"自动添加协议前缀，格式化后的base_url: {base_url}")
        

        
        # 添加API配置
        if hasattr(model, 'api_key'):
            model.api_key = settings.get('api_key', '')
        if hasattr(model, 'base_url'):
            model.base_url = base_url
        else:
            # 如果模型没有base_url属性，动态添加
            setattr(model, 'api_key', settings.get('api_key', ''))
            setattr(model, 'base_url', base_url)
        
        return model
    
    def _extract_context_info(self, context: Dict) -> Dict[str, str]:
        """提取上下文信息"""
        return {
            'grade': context.get('grade', ''),
            'subject': context.get('subject', ''),
            'topic': context.get('topic', ''),
            'article_type': context.get('article_type', ''),
            'requirement': context.get('requirement', '')
        }
    
    def generate_topic(self, grade: str, subject: str, article_type: str, 
                      user_settings: Optional[Dict] = None, requirement: str = None) -> str:
        """生成写作题目"""
        settings = self._get_ai_settings(user_settings)
        model = self._create_llm_model(settings)
        
        # 根据学科选择语言
        is_english = subject and "英语" in subject
        
        if is_english:
            prompt = f"""Please generate an {article_type} topic for {grade} English students that encourages authentic American student writing style.

Requirements:
1. Suitable for {grade} students' cognitive and emotional development
2. Encourages personal reflection and critical thinking
3. Relates to American student life experiences and cultural context
4. Allows for authentic voice and meaningful expression
5. Promotes deep understanding rather than surface-level writing"""
            
            if requirement:
                prompt += f"\n5. Special requirements: {requirement}"
            
            prompt += "\n\nPlease provide the topic directly without additional explanation."
        else:
            prompt = f"""请为{grade}{subject}学生生成一个{article_type}题目。

要求：
1. 符合{grade}学生认知水平
2. 有思考深度和写作空间
3. 贴近学生生活经验
4. 激发写作兴趣"""
            
            if requirement:
                prompt += f"\n5. 特殊要求：{requirement}"
            
            prompt += "\n\n请直接给出题目，不需要额外解释。"
        
        try:
            result = quick_generate(
                prompt=prompt,
                model=model,
                max_tokens=100,
                grade=grade,
                subject=subject,
                requirement=requirement,
                temperature=0.8  # 提高创造性
            )
            return result.strip()
        except Exception as e:
            raise Exception(f"生成题目失败: {str(e)}")
    
    def analyze_content(self, content: str, stage: str, context: Dict, 
                       user_settings: Optional[Dict] = None) -> Dict:
        """分析写作内容"""
        settings = self._get_ai_settings(user_settings)
        model = self._create_llm_model(settings)
        
        # 提取上下文信息
        ctx_info = self._extract_context_info(context)
        
        stage_names = {
            "brainstorm": "构思",
            "outline": "提纲",
            "writing": "正文"
        }
        
        stage_name = stage_names.get(stage, "内容")
        
        # 根据学科制作不同的提示词
        if ctx_info['subject'] == '英语':
            prompt = f"""As an experienced American English writing instructor, please analyze this student's {stage_name} with the perspective of American academic writing standards.

Topic: {ctx_info['topic']}
Student's Content:
{content}

Please analyze the content with American student writing style in mind, focusing on:
1. Content comprehension and meaning development
2. American writing conventions (thesis statements, topic sentences, transitions)
3. Voice, tone, and authentic expression
4. Critical thinking and argument development
5. Grammar and style appropriate for American academic writing

Provide constructive feedback that helps the student write like an American student would, with natural flow and authentic voice.

请用JSON格式回复，包含以下字段（讲解文字用中文，示范文字用英文）：
- strengths: 优点列表（中文讲解）
- issues: 问题列表（中文讲解）
- suggestions: 改进建议列表（中文讲解，英文示例要体现美国学生写作风格）
- next_steps: 下一步建议列表（中文讲解）"""
        else:
            prompt = f"""作为专业的{ctx_info['subject']}写作指导老师，请分析学生的{stage_name}：

{content}

请从以下方面给出建议：
1. 优点和亮点
2. 存在的问题
3. 具体改进建议
4. 下一步建议

请用JSON格式回复，包含以下字段：
- strengths: 优点列表
- issues: 问题列表
- suggestions: 改进建议列表
- next_steps: 下一步建议列表"""
        
        try:
            result = quick_generate(
                prompt=prompt,
                model=model,
                max_tokens=600,
                grade=ctx_info['grade'],
                subject=ctx_info['subject'],
                topic=ctx_info['topic'],
                requirement=f"分析{stage_name}阶段的写作内容",
                json_mode=True,  # 启用JSON模式
                temperature=0.3  # 降低温度以提高准确性
            )
            
            # 尝试解析JSON响应
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # 如果仍然失败，返回结构化的默认响应
                return {
                    "strengths": ["内容已提交"],
                    "issues": ["AI分析格式异常"],
                    "suggestions": ["建议重新分析"],
                    "next_steps": ["继续完善内容"],
                    "raw_response": result
                }
        except Exception as e:
            raise Exception(f"分析内容失败: {str(e)}")
    
    def evaluate_article(self, content: str, context: Dict, 
                        user_settings: Optional[Dict] = None) -> Dict:
        """评估文章质量"""
        settings = self._get_ai_settings(user_settings)
        model = self._create_llm_model(settings)
        
        # 提取上下文信息
        ctx_info = self._extract_context_info(context)
        
        # 根据学科制作不同的提示词
        if ctx_info['subject'] == '英语':
            prompt = f"""As an experienced American English teacher, please evaluate this {ctx_info['article_type']} using American academic writing standards.

Topic: {ctx_info['topic']}
Student's Essay:
{content}

Evaluation should focus on American student writing expectations:
1. Content & Ideas (25 points): Clear thesis, meaningful content, critical thinking, understanding of topic
2. Organization & Structure (25 points): American essay structure (intro-body-conclusion), logical flow, effective transitions
3. Voice & Style (25 points): Authentic American student voice, appropriate tone, natural expression, sentence variety
4. Conventions & Mechanics (25 points): Grammar, spelling, punctuation appropriate for American English

Consider how well the student demonstrates understanding of the topic and expresses ideas in a way that sounds natural for an American student.

请用JSON格式回复，包含以下字段（讲解文字用中文，示范文字用英文）：
- overall_score: 总分（0-100）
- scores: 各维度得分对象 {{"content": 分数, "structure": 分数, "language": 分数, "innovation": 分数}}
- strengths: 优点列表（中文讲解）
- improvements: 改进建议列表（中文讲解，英文示例要体现美国学生写作风格）
- comment: 总体评价（中文）"""
        else:
            prompt = f"""请评估这篇{ctx_info['article_type']}：

{content}

评估维度：
1. 内容质量（25分）：主题明确、内容充实、观点鲜明
2. 结构组织（25分）：层次清晰、逻辑合理、过渡自然
3. 语言表达（25分）：用词准确、句式多样、表达流畅
4. 创新亮点（25分）：观点新颖、表达独特、有个人特色

请用JSON格式回复，包含以下字段：
- overall_score: 总分（0-100）
- scores: 各维度得分对象 {{"content": 分数, "structure": 分数, "language": 分数, "innovation": 分数}}
- strengths: 优点列表
- improvements: 改进建议列表
- comment: 总体评价"""
        
        try:
            result = quick_generate(
                prompt=prompt,
                model=model,
                max_tokens=800,
                grade=ctx_info['grade'],
                subject=ctx_info['subject'],
                topic=ctx_info['topic'],
                requirement=f"评估{ctx_info['article_type']}质量",
                json_mode=True,
                temperature=0.2  # 低温度确保评估一致性
            )
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # 返回默认评估结果，确保分数在正确范围内
                return {
                    "overall_score": 60,
                    "scores": {
                        "content": 15,
                        "structure": 14,
                        "language": 16,
                        "innovation": 15
                    },
                    "strengths": ["文章已完成"],
                    "improvements": ["AI评估格式异常，建议重新评估"],
                    "comment": "文章内容良好，建议继续完善。",
                    "raw_response": result
                }
        except Exception as e:
            raise Exception(f"评估文章失败: {str(e)}")
    
    def generate_suggestions(self, content: str, context: Dict, 
                           suggestion_type: str = "improvement",
                           user_settings: Optional[Dict] = None) -> List[str]:
        """生成写作建议"""
        settings = self._get_ai_settings(user_settings)
        model = self._create_llm_model(settings)
        
        ctx_info = self._extract_context_info(context)
        
        suggestion_prompts = {
            "improvement": "请提供5条具体的改进建议",
            "continuation": "请提供5条继续写作的建议",
            "structure": "请提供5条结构优化建议",
            "language": "请提供5条语言表达建议"
        }
        
        # 添加时间戳和内容信息以确保每次生成不同建议
        import time
        timestamp = int(time.time())
        content_length = len(content)
        content_hash = hash(content) % 10000
        
        prompt = f"""基于以下{ctx_info['article_type']}内容，{suggestion_prompts.get(suggestion_type, '请提供建议')}：

{content}

请以JSON格式回复，包含suggestions字段，内容为建议列表。

注意：当前时间戳：{timestamp}，内容长度：{content_length}字，请基于当前文本的具体内容生成全新的、不重复的建议。"""
        
        try:
            result = quick_generate(
                prompt=prompt,
                model=model,
                max_tokens=400,
                grade=ctx_info['grade'],
                subject=ctx_info['subject'],
                topic=ctx_info['topic'],
                requirement=f"生成{suggestion_type}建议-{content_hash}",
                json_mode=True,
                temperature=0.8  # 增加随机性
            )
            
            try:
                data = json.loads(result)
                return data.get('suggestions', [])
            except json.JSONDecodeError:
                # 提取建议列表
                import re
                suggestions = re.findall(r'\d+\.?\s*(.+)', result)
                return suggestions[:5] if suggestions else ["建议重新生成"]
        except Exception as e:
            return [f"生成建议失败: {str(e)}"]
    
    def generate_stage_suggestions(self, content: str, stage: str, context: Dict,
                                 user_settings: Optional[Dict] = None) -> Dict:
        """生成阶段特定的写作建议"""
        logger.debug(f"[方法调用] generate_stage_suggestions开始")
        logger.debug(f"[输入参数] stage: {stage}")
        logger.debug(f"[输入参数] content长度: {len(content) if content else 0}")
        logger.debug(f"[输入参数] content内容: '{content[:100]}...' (前100字符)" if content else "[输入参数] content为空")
        logger.debug(f"[输入参数] context: {context}")
        
        settings = self._get_ai_settings(user_settings)
        model = self._create_llm_model(settings)
        
        ctx_info = self._extract_context_info(context)
        logger.debug(f"[上下文信息] ctx_info: {ctx_info}")
        
        stage_prompts = {
            "brainstorm": {
                "title": "构思阶段建议",
                "focus": "思路整理、素材收集、观点确立",
                "tips": [
                    "围绕题目核心思考多个角度",
                    "收集相关的事例和素材",
                    "确定文章的主要观点",
                    "考虑读者的兴趣点",
                    "思考文章的创新之处"
                ],
                "example_type": "构思要点"
            },
            "outline": {
                "title": "提纲阶段建议", 
                "focus": "结构安排、逻辑梳理、段落规划",
                "tips": [
                    "确定文章的基本结构（总分总等）",
                    "安排各段落的主要内容",
                    "理清段落间的逻辑关系",
                    "设计好开头和结尾",
                    "确保内容层次分明"
                ],
                "example_type": "提纲条目"
            },
            "writing": {
                "title": "正文阶段建议",
                "focus": "语言表达、细节描述、情感表达",
                "tips": [
                    "用词准确生动",
                    "句式富有变化",
                    "适当运用修辞手法",
                    "注意段落间的过渡",
                    "保持语言风格统一"
                ],
                "example_type": "优美句子"
            }
        }
        
        stage_info = stage_prompts.get(stage, stage_prompts["writing"])
        
        # 获取完整内容用于上下文分析
        full_content = context.get('full_content', {})
        current_stage_text = context.get('current_stage_text', stage)
        
        # 根据学科制作不同的提示词
        if ctx_info['subject'] == '英语':
            prompt = f"""As an experienced American English writing instructor, please provide comprehensive guidance for {ctx_info['grade']} students in the """ + stage_info['title'] + """ stage, focusing on American academic writing style.

Topic: {ctx_info['topic']}
Current Stage: {current_stage_text}
Student's Current Content in {current_stage_text}:
{content if content else '(No content entered yet)'}

Full Writing Context:
- Brainstorm: {full_content.get('brainstorm', '(Empty)')}
- Outline: {full_content.get('outline', '(Empty)')}
- Writing: {full_content.get('writing', '(Empty)')}

Please provide:
1. **Current Status Critique**: Analyze the student's current progress, identify strengths and areas for improvement
2. **Stage-specific guidance** (3-5 items) - help with American writing conventions for this stage
3. **Content development suggestions** (3-5 items) - deepen understanding and meaning
4. **Writing techniques** (3-5 items) - American style and voice
5. **Reference materials** (2-3 items) - authentic American sources
6. **Next steps** (2-3 items) - progression in American academic writing
7. **Three continuation sets**: Provide 3 different ways to continue from the current text, each with exactly 2 sentences that maintain authentic American student voice

请用JSON格式回复，包含以下字段（讲解文字用中文，示范文字用英文）：
- current_status_critique: 当前状态点评（中文分析）
- stage_tips: 阶段特定建议列表（中文讲解）
- content_suggestions: 内容建议列表（中文讲解）
- writing_tips: 写作技巧列表（中文讲解）
- references: 参考素材列表（中文讲解）
- next_steps: 下一步建议列表（中文讲解）
- continuation_sets: 续写建议列表，格式为[{"sentences": ["句子1", "句子2"]}, {"sentences": ["句子1", "句子2"]}, {"sentences": ["句子1", "句子2"]}]（英文续写，体现美国学生自然写作风格）
- example_sentences: 示范" + stage_info['example_type'] + "列表（英文示例，不能重复用户已输入的内容，要提供新的、不同的示范句子）"""
        else:
            prompt = f"""作为专业的{ctx_info['subject']}写作指导老师，请为{ctx_info['grade']}学生的""" + stage_info['title'] + """提供全面指导。

题目：{ctx_info['topic']}
当前阶段：{current_stage_text}
学生在{current_stage_text}阶段的内容：
{content if content else '（尚未输入内容）'}

完整写作上下文：
- 构思内容：{full_content.get('brainstorm', '（空）')}
- 提纲内容：{full_content.get('outline', '（空）')}
- 正文内容：{full_content.get('writing', '（空）')}

请提供：
1. **当前状态点评**：分析学生目前的写作进展，指出优点和需要改进的地方
2. **阶段特定建议**（3-5条）- 针对当前{current_stage_text}阶段的具体指导
3. **内容发展建议**（3-5条）- 如何深化理解和表达
4. **写作技巧**（3-5条）- 提升写作水平的方法
5. **参考素材**（2-3条）- 相关的参考资料或例子
6. **下一步建议**（2-3条）- 如何继续完善
7. **三套续写建议**：基于当前文本，提供3种不同的续写方向，每套包含恰好2句话的续写内容

请用JSON格式回复，包含以下字段：
- current_status_critique: 当前状态点评
- stage_tips: 阶段特定建议列表
- content_suggestions: 内容建议列表
- writing_tips: 写作技巧列表
- references: 参考素材列表
- next_steps: 下一步建议列表
- continuation_sets: 续写建议列表，格式为[{"sentences": ["句子1", "句子2"]}, {"sentences": ["句子1", "句子2"]}, {"sentences": ["句子1", "句子2"]}]
- example_sentences: 示范" + stage_info['example_type'] + "列表（每个示例都要与题目紧密相关，但不能重复用户已输入的内容，要提供新的、不同的示范句子）"""
        
        # 添加时间戳和内容长度信息以确保每次生成不同建议
        import time
        timestamp = int(time.time())
        content_length = len(content)
        content_hash = hash(content) % 10000  # 简单的内容哈希
        
        # 在提示词中添加变化信息和防重复指令
        user_content_preview = content[:100] + '...' if len(content) > 100 else content
        enhanced_prompt = prompt + f"\n\n重要提醒：\n1. 当前时间戳：{timestamp}，内容长度：{content_length}字\n2. 用户当前输入的内容是：『{user_content_preview}』\n3. 示范语句绝对不能包含或重复上述用户输入的任何文字内容\n4. 示范语句必须是全新创作的、与用户输入完全不同的内容\n5. 每次调用都应该提供不同的建议和续写方案\n6. 示范语句要体现该阶段的写作特点，但内容要完全不同于用户输入"
        
        try:
            result = quick_generate(
                prompt=enhanced_prompt,
                model=model,
                max_tokens=1000,
                grade=ctx_info['grade'],
                subject=ctx_info['subject'],
                topic=ctx_info['topic'],
                requirement=f"{stage_info['title']}指导-{content_hash}",
                json_mode=True,
                temperature=0.8  # 增加随机性
            )
            
            try:
                logger.debug(f"[AI响应] 原始AI响应: {result[:200]}...")
                
                # 清理AI响应中的markdown代码块标记
                cleaned_result = result.strip()
                if cleaned_result.startswith('```json'):
                    cleaned_result = cleaned_result[7:]  # 移除开头的```json
                if cleaned_result.endswith('```'):
                    cleaned_result = cleaned_result[:-3]  # 移除结尾的```
                cleaned_result = cleaned_result.strip()
                
                logger.debug(f"[AI响应] 清理后的响应: {cleaned_result[:200]}...")
                data = json.loads(cleaned_result)
                logger.debug(f"[AI响应] JSON解析成功，包含字段: {list(data.keys())}")
                
                # 记录AI生成的example_sentences
                if 'example_sentences' in data:
                    logger.debug(f"[AI生成] example_sentences数量: {len(data['example_sentences'])}")
                    for i, example in enumerate(data['example_sentences']):
                        logger.debug(f"[AI生成] example_sentences[{i}]: {example}")
                else:
                    logger.debug("[AI生成] 未包含example_sentences字段")
                
                # 记录AI生成的continuation_sets
                if 'continuation_sets' in data:
                    logger.debug(f"[AI生成] continuation_sets数量: {len(data['continuation_sets'])}")
                    for i, cont_set in enumerate(data['continuation_sets']):
                        logger.debug(f"[AI生成] continuation_sets[{i}]: {cont_set}")
                    
                    # 处理continuation_sets数据格式
                    processed_continuation_sets = []
                    for cont_set in data['continuation_sets']:
                        if isinstance(cont_set, list):
                            # 如果是数组格式，转换为对象格式
                            processed_continuation_sets.append({"sentences": cont_set})
                        elif isinstance(cont_set, dict) and 'sentences' in cont_set:
                            # 如果已经是正确的对象格式，直接使用
                            processed_continuation_sets.append(cont_set)
                        else:
                            logger.debug(f"[数据处理] 跳过无效的continuation_set: {cont_set}")
                    
                    data['continuation_sets'] = processed_continuation_sets
                    logger.debug(f"[数据处理] 处理后的continuation_sets: {data['continuation_sets']}")
                else:
                    logger.debug("[AI生成] 未包含continuation_sets字段")
                
                # 确保所有字段都存在
                default_suggestions = {
                    "stage_tips": stage_info['tips'],
                    "content_suggestions": ["根据题目要求展开内容", "注意内容的逻辑性"],
                    "writing_tips": ["语言要准确生动", "注意表达的清晰性"],
                    "references": ["可参考相关书籍", "可借鉴优秀范文"],
                    "next_steps": ["继续完善内容", "检查语言表达"],
                    "continuation_sets": [
                        {"title": "方案一", "content": "继续深入分析当前话题的重要性"},
                        {"title": "方案二", "content": "从不同角度探讨相关问题"},
                        {"title": "方案三", "content": "结合具体实例进行论证"}
                    ],
                    "example_sentences": self._get_default_examples(stage, ctx_info['topic'], ctx_info['subject'])
                }
                
                # 合并默认建议和AI生成的建议
                for key in default_suggestions:
                    if key not in data or not data[key]:
                        logger.debug(f"[字段补充] 使用默认值补充字段: {key}")
                        data[key] = default_suggestions[key]
                
                # 检查并过滤示范语句中与用户输入相同的内容
                if 'example_sentences' in data and data['example_sentences']:
                    logger.debug(f"[过滤前] example_sentences: {data['example_sentences']}")
                    
                    # 处理不同的example_sentences数据结构
                    examples_to_process = []
                    if isinstance(data['example_sentences'], dict):
                        # 如果是对象结构，提取实际的示范句子
                        if 'example_sentences' in data['example_sentences']:
                            examples_to_process = data['example_sentences']['example_sentences']
                        elif 'example' in data['example_sentences']:
                            examples_to_process = [data['example_sentences']['example']]
                        else:
                            # 尝试提取所有字符串值
                            for key, value in data['example_sentences'].items():
                                if isinstance(value, str) and len(value) > 10:  # 过滤掉短标识符
                                    examples_to_process.append(value)
                    elif isinstance(data['example_sentences'], list):
                        examples_to_process = data['example_sentences']
                    else:
                        examples_to_process = []
                    
                    logger.debug(f"[数据处理] 提取到的示范句子: {examples_to_process}")
                    
                    filtered_examples = []
                    user_content_lower = content.lower().strip() if content else ''
                    logger.debug(f"[用户输入] 小写处理后: '{user_content_lower}'")
                    
                    for i, example in enumerate(examples_to_process):
                        if isinstance(example, str):
                            example_lower = example.lower().strip()
                            logger.debug(f"[过滤检查] example[{i}]: '{example}' -> '{example_lower}'")
                            
                            # 如果示范语句与用户输入内容不同，才保留
                            if example_lower != user_content_lower and user_content_lower not in example_lower:
                                filtered_examples.append(example)
                                logger.debug(f"[过滤结果] example[{i}] 保留")
                            else:
                                logger.debug(f"[过滤结果] example[{i}] 被过滤 (重复或包含用户输入)")
                    
                    logger.debug(f"[过滤后] 保留的example_sentences数量: {len(filtered_examples)}")
                    
                    # 如果过滤后没有示范语句，使用默认示范语句
                    if not filtered_examples:
                        logger.debug("[默认值] 过滤后无示范语句，使用默认值")
                        data['example_sentences'] = self._get_default_examples(stage, ctx_info['topic'], ctx_info['subject'])
                        logger.debug(f"[默认值] 默认example_sentences: {data['example_sentences']}")
                    else:
                        data['example_sentences'] = filtered_examples
                        logger.debug(f"[最终结果] 使用过滤后的example_sentences: {data['example_sentences']}")
                
                return data
                
            except json.JSONDecodeError as e:
                # 如果JSON解析失败，返回阶段默认建议
                logger.error(f"[JSON解析失败] 错误: {str(e)}")
                logger.error(f"[JSON解析失败] 原始响应: {result}")
                default_examples = self._get_default_examples(stage, ctx_info['topic'], ctx_info['subject'])
                logger.debug(f"[JSON解析失败] 使用默认example_sentences: {default_examples}")
                return {
                    "stage_tips": stage_info['tips'],
                    "content_suggestions": [
                        "围绕题目核心展开内容",
                        "注意内容的层次性和逻辑性",
                        "结合个人经历和感受"
                    ],
                    "writing_tips": [
                        "语言要准确生动",
                        "适当运用修辞手法",
                        "注意句式的变化"
                    ],
                    "references": [
                        "可参考相关经典作品",
                        "关注时事热点素材"
                    ],
                    "next_steps": [
                        "继续完善当前阶段内容",
                        "准备进入下一写作阶段"
                    ],
                    "continuation_sets": [
                        {"title": "方案一", "content": "继续深入分析当前话题的重要性"},
                        {"title": "方案二", "content": "从不同角度探讨相关问题"},
                        {"title": "方案三", "content": "结合具体实例进行论证"}
                    ],
                    "example_sentences": default_examples,
                    "raw_response": result
                }
        except Exception as e:
            # 返回基础建议
            logger.error(f"[异常处理] 发生异常: {str(e)}")
            logger.error(f"[异常处理] 异常类型: {type(e).__name__}")
            default_examples = self._get_default_examples(stage, ctx_info['topic'], ctx_info['subject'])
            logger.debug(f"[异常处理] 使用默认example_sentences: {default_examples}")
            return {
                "stage_tips": stage_info['tips'],
                "content_suggestions": ["请根据题目要求继续完善内容"],
                "writing_tips": ["注意语言的准确性和生动性"],
                "references": ["可参考相关优秀作品"],
                "next_steps": ["继续当前阶段的写作"],
                "continuation_sets": [
                    {"title": "方案一", "content": "继续深入分析当前话题的重要性"},
                    {"title": "方案二", "content": "从不同角度探讨相关问题"},
                    {"title": "方案三", "content": "结合具体实例进行论证"}
                ],
                "example_sentences": default_examples,
                "error": str(e)
            }
    
    def _get_default_examples(self, stage: str, topic: str, subject: str = '语文') -> List[str]:
        """获取默认示范语句"""
        if subject == '英语':
            # 英语学科的全英文示范语句，根据阶段写相应的文章句子
            if stage == "brainstorm":
                return [
                    "I want to explore this from multiple angles to develop a comprehensive understanding.",
                    "My personal experience with this has shaped my perspective in meaningful ways.",
                    "There are several key aspects that deserve careful consideration and analysis."
                ]
            elif stage == "outline":
                return [
                    "I. Introduction: Hook the reader with a compelling opening and clear thesis statement",
                    "II. Body: Present evidence and analysis with smooth transitions between ideas",
                    "III. Conclusion: Synthesize main points and leave the reader with lasting thoughts"
                ]
            else:  # writing
                return [
                    "As I reflect on this experience, I realize how profoundly it has influenced my worldview.",
                    "The complexity of this issue becomes apparent when we examine it from different perspectives.",
                    "This moment taught me something valuable about myself and the world around me."
                ]
        else:
            # 语文学科的中文示范语句，根据阶段写相应的文章句子
            if stage == "brainstorm":
                return [
                    "我想从多个角度来深入思考这个问题，寻找不同的切入点。",
                    "这个话题让我联想到生活中的许多真实经历和感受。",
                    "我需要仔细分析其中蕴含的深层含义和价值。"
                ]
            elif stage == "outline":
                return [
                    "一、开头：用生动的场景或深刻的感悟引入主题",
                    "二、主体：通过具体事例和细致描写展开论述",
                    "三、结尾：升华主题，表达个人感悟和思考"
                ]
            else:  # writing
                return [
                    "那一刻，我深深地感受到了内心的震撼和思考的力量。",
                    "生活中的点点滴滴都在诉说着一个深刻的道理。",
                    "这次经历让我对人生有了更加深刻的理解和感悟。"
                ]
    
    def test_connection(self, user_settings: Dict) -> bool:
        """测试AI连接"""
        try:
            settings = self._get_ai_settings(user_settings)
            model = self._create_llm_model(settings)
            return quick_test(model)
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试默认配置
            model = self._create_llm_model(self.default_settings)
            connection_ok = quick_test(model)
            
            return {
                "status": "healthy" if connection_ok else "unhealthy",
                "connection": connection_ok,
                "default_model": self.default_settings['model'],
                "default_provider": self.default_settings['provider']
            }
        except Exception as e:
            return {
                "status": "error",
                "connection": False,
                "error": str(e)
            }

# 全局AI服务实例
ai_service = AIService()

# 同步包装函数，用于在非异步环境中调用
def sync_generate_topic(grade: str, subject: str, article_type: str, 
                       user_settings: Optional[Dict] = None, requirement: str = None) -> str:
    """同步生成题目"""
    return ai_service.generate_topic(grade, subject, article_type, user_settings, requirement)

def sync_analyze_content(content: str, stage: str, context: Dict, 
                        user_settings: Optional[Dict] = None) -> Dict:
    """同步分析内容"""
    return ai_service.analyze_content(content, stage, context, user_settings)

def sync_evaluate_article(content: str, context: Dict, 
                         user_settings: Optional[Dict] = None) -> Dict:
    """同步评估文章"""
    return ai_service.evaluate_article(content, context, user_settings)

def sync_generate_suggestions(content: str, context: Dict, suggestion_type: str = "improvement",
                            user_settings: Optional[Dict] = None) -> List[str]:
    """同步生成建议"""
    return ai_service.generate_suggestions(content, context, suggestion_type, user_settings)

def sync_generate_stage_suggestions(content: str, stage: str, context: Dict,
                                  user_settings: Optional[Dict] = None) -> Dict:
    """同步生成阶段特定建议"""
    return ai_service.generate_stage_suggestions(content, stage, context, user_settings)

def sync_test_connection(user_settings: Dict) -> bool:
    """同步测试连接"""
    return ai_service.test_connection(user_settings)

def sync_health_check() -> Dict[str, Any]:
    """同步健康检查"""
    return ai_service.health_check()