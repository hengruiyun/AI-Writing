"""
文章打分标准系统
Article Scoring Standards System

根据构思10%，提纲0%，正文60%，爆点30%的比例计算总分
各项指标由LLM分项打分后汇总计算
"""

class ArticleScoringStandards:
    """文章打分标准类"""
    
    # 各阶段权重配置
    STAGE_WEIGHTS = {
        'brainstorm': 0.10,  # 构思 10%
        'outline': 0.00,     # 提纲 0%（不再计算得分）
        'writing': 0.60,     # 正文 60%
        'highlight': 0.30    # 爆点 30%
    }
    
    # 评分标准定义
    SCORING_CRITERIA = {
        'brainstorm': {
            'name': '构思评分',
            'description': '基于正文与构思相似度进行评分，相似度直接对应得分',
            'criteria': [
                '相似度计算：将正文总结概括后，与构思进行相似度比较',
                '得分规则：故事相似度百分比直接对应得分（如相似50%得50分）',
                '内容一致性：正文是否忠实体现了构思的核心思想',
                '主题贯彻：正文是否围绕构思主题展开',
                '执行度：构思中的要点在正文中的体现程度'
            ],
            'similarity_scoring': {
                '计算方法': '使用故事相似度算法比较正文摘要与构思内容',
                '得分公式': '构思得分 = 相似度百分比（0-100）',
                '相似度阈值': {
                    '90-100%': '正文完全体现构思内容，高度一致',
                    '70-89%': '正文大部分体现构思内容，基本一致',
                    '50-69%': '正文部分体现构思内容，中等一致',
                    '40-49%': '正文少量体现构思内容，一致性较低',
                    '0-39%': '正文基本未体现构思内容，一致性极低'
                }
            },
            'evaluation_process': {
                '步骤1': '提取正文核心内容，',
                '步骤2': '正文核心内容与构思进行故事相似度计算',
                '步骤3': '相似度百分比直接作为构思得分',
                '步骤4': '提供详细的相似度分析说明'
            },
            'scoring_guide': {
                '90-100': '正文与构思高度相似，完全按构思执行',
                '70-89': '正文与构思大部分相似，基本按构思执行',
                '50-69': '正文与构思中等相似，部分按构思执行',
                '40-49': '正文与构思相似度较低，偏离构思较多',
                '0-39': '正文与构思相似度极低，基本偏离构思'
            }
        },
        
        'outline': {
            'name': '提纲评分',
            'description': '评估文章结构提纲的完整性和逻辑性',
            'criteria': [
                '结构完整性：提纲是否包含开头、主体、结尾等完整结构',
                '层次清晰性：各级标题是否层次分明，逻辑清晰',
                '内容关联性：各部分内容是否紧密关联，服务于主题',
                '详细程度：提纲是否足够详细，便于后续写作',
                '可操作性：提纲是否具有实际的指导价值'
            ],
            'scoring_guide': {
                90-100: '提纲结构完整，层次清晰，内容关联性强，详细且可操作',
                80-89: '提纲结构较完整，层次较清晰，内容关联性较好',
                70-79: '提纲结构基本完整，层次基本清晰，内容有一定关联性',
                60-69: '提纲结构不够完整，层次不够清晰，内容关联性一般',
                0-59: '提纲结构不完整，层次混乱，内容关联性差'
            }
        },
        
        'writing': {
            'name': '正文评分',
            'description': '评估文章正文的质量和表达效果，采用详细分项评分标准',
            'criteria': [
                '内容质量（20分）：内容充实度、信息准确性、论述深度、事实依据、数据支撑',
                '语言表达（15分）：语言流畅性、表达清晰度、文字优美度、词汇丰富性、句式变化',
                '逻辑结构（10分）：段落安排合理性、逻辑清晰度、过渡自然性、层次分明度',
                '完整性（5分）：内容完整度、提纲展开充分性、结构完整性',
                '可读性（10分）：易读性、吸引力、节奏感'
            ],
            'detailed_requirements': {
                '内容质量': {
                    '充实度': '不少于3段，每段内容不少于3个要点，论述深入具体',
                    '准确性': '事实准确，数据可靠，引用恰当',
                    '深度': '分析透彻，见解独到，论证有力',
                    '依据': '有理有据，逻辑严密，论证充分',
                    '支撑': '数据支撑有力，案例恰当，证据充分'
                },
                '语言表达': {
                    '流畅性': '语句通顺，表达自然，无语病',
                    '清晰度': '表意明确，无歧义，易理解',
                    '优美度': '文字优美，富有感染力',
                    '丰富性': '词汇丰富，用词准确，避免重复',
                    '变化性': '句式多样，长短结合，富有节奏'
                },
                '逻辑结构': {
                    '合理性': '段落安排合理，层次清晰',
                    '清晰度': '逻辑链条清晰，因果关系明确',
                    '自然性': '过渡自然，衔接流畅',
                    '分明度': '主次分明，重点突出'
                },
                '完整性': {
                    '完整度': '内容完整，无缺失',
                    '文章长度': '字数达2000字以上',
                    '展开性': '按提纲充分展开，不偏题',
                    '结构性': '开头、主体、结尾结构完整'
                },
                '可读性': {
                    '易读性': '通俗易懂，适合目标读者',
                    '吸引力': '引人入胜，保持读者兴趣'
                }
            },
            'scoring_guide': {
                '85-100': '各项要求全部达到，正文质量极高，内容充实准确，语言优美流畅，逻辑清晰，完整性强，可读性佳',
                '71-84': '大部分要求达到，正文质量优秀，内容充实，语言较流畅，逻辑较清晰，基本完整',
                '60-70': '多数要求达到，正文质量良好，内容基本充实，语言基本流畅，逻辑基本清晰',
                '50-59': '部分要求达到，正文质量一般，内容不够充实，语言表达一般，逻辑有待改进',
                '0-49': '要求达到较少，正文质量较差，内容空洞，语言表达不清，逻辑混乱'
            },
            'deduction_rules': {
                '缺少内容质量要素': '每缺少一项扣10分',
                '缺少语言表达要素': '每缺少一项扣10分',
                '缺少逻辑结构要素': '每缺少一项扣5分',
                '缺少完整性要素': '每缺少一项扣10分',
                '缺少可读性要素': '每缺少一项扣10分'
            }
        },
        
        'highlight': {
            'name': '爆点评分',
            'description': '评估文章的亮点和吸引力，重点考察创新指数，常见写法得分较低',
            'criteria': [
                '创新指数（核心）：观点、角度、表达方式的独创性和新颖度',
                '差异化程度：与常见写法的区别度，避免套路化表达',
                '突破性思维：是否打破常规思维模式，提出独特见解',
                '表达创新：语言表达、结构安排、呈现方式的创新性',
                '价值独特性：提供的价值和信息是否具有独特性和稀缺性'
            ],
            'innovation_index': {
                '极高创新（90-100分）': '完全原创的观点和表达，前所未见的角度，颠覆性思维',
                '高度创新（70-89分）': '大部分内容具有创新性，少量借鉴但有显著改进',
                '中等创新（60-69分）': '有一定创新元素，但仍有常见表达方式',
                '低度创新（50-59分）': '创新元素较少，多为常见写法的变形',
                '无创新（0-49分）': '完全是常见写法，套路化表达，无新意'
            },
            'common_patterns_penalty': {
                '套路化开头': '使用"在这个...的时代"等常见开头扣15分',
                '陈词滥调': '使用老生常谈的表达方式扣10分',
                '模板化结构': '完全按照固定模板写作扣10-20分',
                '空洞口号': '使用空洞的口号式表达扣15分',
                '千篇一律': '与大众化写法高度相似扣20-30分'
            },
            'innovation_bonus': {
                '独特视角': '提供全新视角加5-10分',
                '创新表达': '语言表达富有创意加5-15分',
                '结构创新': '文章结构安排新颖加5-10分',
                '思维突破': '打破常规思维加10-20分',
                '原创价值': '提供独特价值和见解加10-25分'
            },
            'scoring_guide': {
                '90-100': '创新指数极高，完全避免常见写法，具有突破性和原创性，令人眼前一亮',
                '80-89': '创新指数较高，大部分内容具有新意，较少使用常见表达',
                '70-79': '创新指数中等，有一定新意但仍有常见元素',
                '60-69': '创新指数较低，多为常见写法，缺乏新意',
                '0-59': '创新指数极低，完全是常见套路，毫无新意'
            }
        }
    }
    
    @classmethod
    def calculate_total_score(cls, scores):
        """
        计算总分
        
        Args:
            scores (dict): 各阶段评分 {'brainstorm': 85, 'outline': 78, 'writing': 88, 'highlight': 92}
        
        Returns:
            float: 总分 (0-100)
        """
        total_score = 0
        for stage, score in scores.items():
            if stage in cls.STAGE_WEIGHTS:
                weighted_score = score * cls.STAGE_WEIGHTS[stage]
                total_score += weighted_score
        
        return int(total_score)
    
    @classmethod
    def get_scoring_prompt(cls, stage, content):
        """
        获取LLM打分提示词
        
        Args:
            stage (str): 评分阶段
            content (str): 待评分内容
        
        Returns:
            str: 打分提示词
        """
        if stage not in cls.SCORING_CRITERIA:
            return ""
        
        criteria = cls.SCORING_CRITERIA[stage]
        
        prompt = f"""
请根据以下标准对{criteria['name']}进行评分：

评分内容：
{content}

评分标准：
{criteria['description']}

具体评分维度：
"""
        
        for i, criterion in enumerate(criteria['criteria'], 1):
            prompt += f"{i}. {criterion}\n"
        
        prompt += f"""
评分参考：
优秀(90-100分)：{criteria['scoring_guide'].get('90-100', '表现优秀')}
良好(80-89分)：{criteria['scoring_guide'].get('80-89', '表现良好')}
一般(70-79分)：{criteria['scoring_guide'].get('70-79', '表现一般')}
需改进(60-69分)：{criteria['scoring_guide'].get('60-69', '需要改进')}
较差(0-59分)：{criteria['scoring_guide'].get('0-59', '表现较差')}

请给出0-100分的评分，并简要说明评分理由。
格式：评分：XX分
理由：[简要说明]
"""
        
        return prompt
    
    @classmethod
    def get_stage_weight(cls, stage):
        """获取阶段权重"""
        return cls.STAGE_WEIGHTS.get(stage, 0)
    
    @classmethod
    def get_all_weights(cls):
        """获取所有权重"""
        return cls.STAGE_WEIGHTS.copy()
    
    @classmethod
    def validate_scores(cls, scores):
        """
        验证评分数据
        
        Args:
            scores (dict): 评分数据
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(scores, dict):
            return False, "评分数据必须是字典格式"
        
        for stage, score in scores.items():
            if stage not in cls.STAGE_WEIGHTS:
                return False, f"未知的评分阶段: {stage}"
            
            if not isinstance(score, (int, float)):
                return False, f"评分必须是数字: {stage}"
            
            if not 0 <= score <= 100:
                return False, f"评分必须在0-100之间: {stage}"
        
        return True, ""
    
    @classmethod
    def get_score_breakdown(cls, scores):
        """
        获取评分详细分解
        
        Args:
            scores (dict): 各阶段评分
        
        Returns:
            dict: 详细分解信息
        """
        breakdown = {
            'stages': {},
            'total_score': 0,
            'weighted_scores': {}
        }
        
        for stage, score in scores.items():
            if stage in cls.STAGE_WEIGHTS:
                weight = cls.STAGE_WEIGHTS[stage]
                weighted_score = score * weight
                
                breakdown['stages'][stage] = {
                    'name': cls.SCORING_CRITERIA[stage]['name'],
                    'raw_score': score,
                    'weight': weight,
                    'weighted_score': weighted_score,
                    'percentage': f"{weight * 100}%"
                }
                
                breakdown['weighted_scores'][stage] = weighted_score
                breakdown['total_score'] += weighted_score
        
        breakdown['total_score'] = int(breakdown['total_score'])
        
        return breakdown


# 使用示例
if __name__ == "__main__":
    # 示例评分
    sample_scores = {
        'brainstorm': 85,  # 构思评分
        'outline': 78,     # 提纲评分
        'writing': 88,     # 正文评分
        'highlight': 92    # 爆点评分
    }
    
    # 计算总分
    total_score = ArticleScoringStandards.calculate_total_score(sample_scores)
    print(f"总分: {total_score}")
    
    # 获取详细分解
    breakdown = ArticleScoringStandards.get_score_breakdown(sample_scores)
    print("\n评分详细分解:")
    for stage, info in breakdown['stages'].items():
        print(f"{info['name']}: {info['raw_score']}分 × {info['percentage']} = {info['weighted_score']:.1f}分")
    print(f"总分: {breakdown['total_score']}分")
    
    # 获取打分提示词示例
    print("\n构思阶段打分提示词:")
    prompt = ArticleScoringStandards.get_scoring_prompt('brainstorm', "这是一个关于人工智能发展的文章构思...")
    print(prompt)