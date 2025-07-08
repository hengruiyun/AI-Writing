#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多视角分析引擎
整合技术分析、基本面分析和风险管理三个视角的分析结果
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from utils import call_llm
from models.analysis_models import (
    MultiPerspectiveAnalysis,
    MarketAnalysis,
    SectorAnalysis,
    StockRecommendation,
    RiskManagement,
    TimeframeOutlook,
    StructuredAnalysisResult
)
from prompts.localized_prompts import LocalizedPrompts, PromptOptimizer

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    role: str
    system_prompt: str
    description: str
    parameters: Dict[str, Any]
    examples: List[Dict[str, str]]
    tags: List[str]
    language: str

class MultiPerspectiveEngine:
    """多视角分析引擎"""
    
    def __init__(self, agents_dir: str = "prompts/agents"):
        self.agents_dir = Path(agents_dir)
        self.agents: Dict[str, AgentConfig] = {}
        self._load_agents()
    
    def _load_agents(self):
        """加载智能体配置"""
        try:
            for agent_file in self.agents_dir.glob("*.json"):
                with open(agent_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    agent_config = AgentConfig(**config_data)
                    self.agents[agent_config.role] = agent_config
                    logger.info(f"已加载智能体: {agent_config.name} ({agent_config.role})")
        except Exception as e:
            logger.error(f"加载智能体配置失败: {e}")
    
    def _build_agent_prompt(self, agent_role: str, market_data: Dict[str, Any]) -> str:
        """构建特定智能体的分析提示"""
        if agent_role not in self.agents:
            raise ValueError(f"未找到智能体: {agent_role}")
        
        # 使用本土化提示词
        if agent_role == 'technical_analyst':
            base_prompt = LocalizedPrompts.get_technical_analysis_prompt(market_data)
        elif agent_role == 'fundamental_analyst':
            base_prompt = LocalizedPrompts.get_fundamental_analysis_prompt(market_data)
        elif agent_role == 'risk_analyst':
            base_prompt = LocalizedPrompts.get_risk_management_prompt(market_data)
        else:
            # 回退到原有方式
            agent = self.agents[agent_role]
            base_prompt = f"{agent.system_prompt}\n\n"
        
        # 添加具体市场数据
        data_section = self._format_market_data(market_data)
        
        # 判断市场状况并优化提示词
        market_condition = self._assess_market_condition(market_data)
        optimized_prompt = PromptOptimizer.optimize_for_market_condition(base_prompt, market_condition)
        
        # 添加风险提示
        final_prompt = PromptOptimizer.add_risk_warning(optimized_prompt)
        
        # 组合最终提示词
        complete_prompt = f"{final_prompt}\n\n{data_section}\n\n请基于以上信息提供结构化的专业分析。"
        
        return complete_prompt
    
    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """格式化市场数据"""
        data_text = "### 📊 当前市场数据\n\n"
        
        # 市场情绪数据
        if 'market_sentiment' in market_data:
            sentiment = market_data['market_sentiment']
            data_text += "**市场情绪指标**\n"
            data_text += f"- 市场情绪指数(MSCI): {sentiment.get('index', 'N/A')}\n"
            data_text += f"- 5日动量趋势: {sentiment.get('momentum_5d', 'N/A')}%\n"
            data_text += f"- 市场波动率: {sentiment.get('volatility', 'N/A')}%\n"
            data_text += f"- 成交量比率: {sentiment.get('volume_ratio', 'N/A')}x\n\n"
        
        # 宏观经济数据
        if 'macro_economy' in market_data:
            macro = market_data['macro_economy']
            data_text += "**宏观经济环境**\n"
            data_text += f"- 基准利率: {macro.get('interest_rate', 'N/A')}%\n"
            data_text += f"- 通胀水平: {macro.get('inflation', 'N/A')}%\n"
            data_text += f"- GDP增速: {macro.get('gdp_growth', 'N/A')}%\n"
            data_text += f"- 货币强度: {macro.get('currency_strength', 'N/A')}/100\n"
            data_text += f"- 市场流动性: {macro.get('market_liquidity', 'N/A')}/100\n\n"
        
        # 新闻情感数据
        if 'news_sentiment' in market_data:
            news = market_data['news_sentiment']
            data_text += "**新闻情感分析**\n"
            data_text += f"- 整体情感倾向: {news.get('sentiment', 'N/A')}\n"
            data_text += f"- 正面消息占比: {news.get('positive_ratio', 0):.1%}\n"
            data_text += f"- 负面消息占比: {news.get('negative_ratio', 0):.1%}\n"
            if news.get('keywords'):
                data_text += f"- 热点关键词: {', '.join(news['keywords'][:5])}\n"
            data_text += "\n"
        
        # 行业数据
        if 'industry_data' in market_data:
            industries = market_data['industry_data']
            data_text += "**行业相对强度指数(IRSI)排名**\n"
            for i, industry in enumerate(industries[:5], 1):
                irsi = industry.get('irsi', 0)
                strength = "强势" if irsi > 60 else "中性" if irsi > 40 else "弱势"
                data_text += f"{i}. {industry.get('name', 'N/A')}: {irsi:.1f} ({strength})\n"
            data_text += "\n"
        
        # 个股数据
        if 'stock_data' in market_data:
            stocks = market_data['stock_data']
            data_text += "**优秀个股TOP5 (RTSI排名)**\n"
            for i, stock in enumerate(stocks[:5], 1):
                rtsi = stock.get('rtsi', 0)
                rating = "强烈推荐" if rtsi > 80 else "推荐" if rtsi > 65 else "中性" if rtsi > 50 else "观望"
                data_text += f"{i}. {stock.get('name', 'N/A')}({stock.get('code', 'N/A')}): RTSI {rtsi:.1f} ({rating})\n"
            data_text += "\n"
        
        # 历史数据
        if 'historical_data' in market_data:
            historical = market_data['historical_data']
            if historical.get('msci_trend'):
                msci_trend = historical['msci_trend']
                if len(msci_trend) >= 2:
                    trend_change = msci_trend[-1] - msci_trend[0]
                    trend_desc = "上升" if trend_change > 0 else "下降" if trend_change < 0 else "平稳"
                    data_text += f"**历史趋势**: 近期MSCI趋势{trend_desc} ({trend_change:+.1f}点)\n\n"
        
        return data_text
    
    def _assess_market_condition(self, market_data: Dict[str, Any]) -> str:
        """评估市场状况"""
        try:
            # 基于MSCI指数判断市场状况
            msci = 50  # 默认值
            if 'market_sentiment' in market_data:
                msci = market_data['market_sentiment'].get('index', 50)
            
            if msci > 70:
                return "牛市"
            elif msci < 30:
                return "熊市"
            else:
                return "震荡市"
                
        except Exception as e:
            logger.warning(f"评估市场状况失败: {e}")
            return "震荡市"
    
    def analyze_single_perspective(self, agent_role: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """单一视角分析"""
        try:
            prompt = self._build_agent_prompt(agent_role, market_data)
            
            # 调用LLM进行分析
            result = call_llm(
                prompt=prompt,
                pydantic_model=StructuredAnalysisResult,
                max_retries=3
            )
            
            return {
                'agent_role': agent_role,
                'agent_name': self.agents[agent_role].name,
                'analysis': result,
                'timestamp': market_data.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"{agent_role}分析失败: {e}")
            return {
                'agent_role': agent_role,
                'agent_name': self.agents.get(agent_role, {}).get('name', 'Unknown'),
                'analysis': None,
                'error': str(e),
                'timestamp': market_data.get('timestamp')
            }
    
    def analyze_multi_perspective(self, market_data: Dict[str, Any]) -> MultiPerspectiveAnalysis:
        """多视角综合分析"""
        try:
            # 并行执行三个视角的分析
            perspectives = ['technical_analyst', 'fundamental_analyst', 'risk_analyst']
            
            results = {}
            for perspective in perspectives:
                if perspective in self.agents:
                    result = self.analyze_single_perspective(perspective, market_data)
                    results[perspective] = result
            
            # 构建多视角分析结果
            multi_analysis = MultiPerspectiveAnalysis(
                technical_perspective=results.get('technical_analyst', {}).get('analysis'),
                fundamental_perspective=results.get('fundamental_analyst', {}).get('analysis'),
                risk_perspective=results.get('risk_analyst', {}).get('analysis'),
                consensus_view=self._generate_consensus(results),
                confidence_score=self._calculate_confidence(results)
            )
            
            return multi_analysis
            
        except Exception as e:
            logger.error(f"多视角分析失败: {e}")
            raise
    
    def _generate_consensus(self, results: Dict[str, Any]) -> str:
        """生成共识观点"""
        try:
            # 简单的共识生成逻辑
            valid_results = [r for r in results.values() if r.get('analysis') is not None]
            
            if not valid_results:
                return "分析数据不足，无法形成共识观点"
            
            # 这里可以实现更复杂的共识算法
            # 目前简单返回一个基于多视角的综合判断
            return f"基于{len(valid_results)}个分析视角的综合判断，建议谨慎操作，关注风险控制。"
            
        except Exception as e:
            logger.error(f"生成共识观点失败: {e}")
            return "共识观点生成失败"
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """计算置信度"""
        try:
            valid_results = [r for r in results.values() if r.get('analysis') is not None]
            
            if not valid_results:
                return 0.0
            
            # 基于有效分析结果数量计算置信度
            confidence = len(valid_results) / len(self.agents) * 0.8
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"计算置信度失败: {e}")
            return 0.0
    
    def get_available_agents(self) -> List[str]:
        """获取可用的智能体列表"""
        return list(self.agents.keys())
    
    def get_agent_info(self, agent_role: str) -> Optional[AgentConfig]:
        """获取智能体信息"""
        return self.agents.get(agent_role)